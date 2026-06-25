from __future__ import annotations

import ast
import json
import logging
import re
import time
from typing import Optional

from llm_utils import extract_json_from_response, initialize_llm_provider
from models import (
    EvaluationData,
    GenericSGEvaluation,
    assert_sg_categories,
)
from prompt import DEFAULT_MODEL, MODEL_PARAMETERS
from prompts.template_manager import DEFAULT_ROLE, TemplateManager, is_sg_role

logger = logging.getLogger(__name__)

# How long (seconds) to wait for the evaluation LLM call.
# 0 = no limit. Increase if you see truncated responses.
EVAL_TIMEOUT = 0

# How many times to retry if the LLM returns incomplete/unparseable output.
MAX_RETRIES = 3


def _parse_llm_json(response_text: str) -> dict:
    """
    Robustly parse LLM output as JSON.
    Handles:
      - Proper JSON with double quotes
      - Python-style dicts with single quotes
      - Trailing commas
      - Extra text before/after the JSON block
      - Incomplete/truncated JSON (attempts to close open braces)
    """
    response_text = response_text.strip()

    # Extract outermost {...} block
    json_start = response_text.find("{")
    json_end = response_text.rfind("}")
    if json_start == -1:
        raise ValueError("LLM response contains no JSON object (no opening brace found).")

    if json_end == -1 or json_end <= json_start:
        # Response was truncated — try to close open braces
        logger.warning("LLM response appears truncated. Attempting to auto-close braces.")
        fragment = response_text[json_start:]
        open_braces = fragment.count("{") - fragment.count("}")
        open_brackets = fragment.count("[") - fragment.count("]")
        fragment = fragment.rstrip(",").rstrip()
        fragment += "]" * max(0, open_brackets)
        fragment += "}" * max(0, open_braces)
        response_text = fragment
    else:
        response_text = response_text[json_start:json_end + 1]

    # Attempt 1: strict JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.debug("json.loads failed (%s), trying fallbacks...", e)

    # Attempt 2: strip trailing commas then retry
    cleaned = re.sub(r",\s*([}\]])", r"\1", response_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 3: ast.literal_eval for Python-style single-quoted dicts
    try:
        parsed = ast.literal_eval(response_text)
        if isinstance(parsed, dict):
            logger.debug("Parsed via ast.literal_eval fallback")
            return parsed
    except Exception:
        pass

    logger.error("Could not parse LLM response as JSON. Raw output:")
    logger.error(response_text)
    raise ValueError(
        "LLM did not return valid JSON after all fallback attempts. "
        "Raw output logged above."
    )


class ResumeEvaluator:
    def __init__(self, model_name: str = DEFAULT_MODEL, model_params: dict | None = None):
        if not model_name:
            raise ValueError("Model name cannot be empty.")

        self.model_name = model_name
        self.model_params = model_params or MODEL_PARAMETERS.get(
            model_name,
            {"temperature": 0.1, "top_p": 0.9},
        )
        self.template_manager = TemplateManager()
        self.provider = initialize_llm_provider(self.model_name)
        logger.info("ResumeEvaluator initialised with model: %s", self.model_name)

    def _call_llm(
        self,
        user_prompt: str,
        system_message: str,
        response_schema: Optional[dict] = None,
    ) -> str:
        kwargs = {}

        # Pass schema only if the model is known to support structured output well.
        # gemma3 can produce truncated output when format is enforced — skip it.
        if response_schema is not None:
            kwargs["format"] = response_schema

        # Apply timeout if set
        if EVAL_TIMEOUT and EVAL_TIMEOUT > 0:
            kwargs["options"] = {"timeout": EVAL_TIMEOUT}

        response = self.provider.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.model_params.get("temperature", 0.1),
            top_p=self.model_params.get("top_p", 0.9),
            **kwargs,
        )

        if isinstance(response, str):
            return response
        if (
            isinstance(response, dict)
            and "message" in response
            and isinstance(response["message"], dict)
            and "content" in response["message"]
        ):
            return response["message"]["content"]
        if hasattr(response, "text"):
            return response.text
        if hasattr(response, "content"):
            return response.content

        raise ValueError("Unexpected LLM response shape: " + str(type(response)))

    def _call_llm_with_retry(
        self,
        user_prompt: str,
        system_message: str,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """
        Calls LLM and retries up to MAX_RETRIES times if output cannot be parsed.
        On retry 2+, drops the response_schema to allow freer output.
        """
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            # After first failure, stop passing format schema — let model respond freely
            schema = response_schema if attempt == 1 else None
            if attempt > 1:
                logger.warning(
                    "Retry %d/%d for LLM evaluation (schema enforcement dropped)...",
                    attempt,
                    MAX_RETRIES,
                )
                time.sleep(1)

            try:
                raw = self._call_llm(
                    user_prompt=user_prompt,
                    system_message=system_message,
                    response_schema=schema,
                )
                raw = extract_json_from_response(raw)
                return _parse_llm_json(raw)
            except Exception as exc:
                logger.warning("Attempt %d failed: %s", attempt, exc)
                last_exc = exc

        raise ValueError(
            "LLM failed to return valid JSON after "
            + str(MAX_RETRIES)
            + " attempts. Last error: "
            + str(last_exc)
        )

    def _build_prompt(
        self,
        resume_text: str,
        role_type: str = DEFAULT_ROLE,
        target_job_title: str = "",
    ) -> tuple[str, str]:
        system_message = self.template_manager.get_system_message(role_type=role_type)
        user_prompt = self.template_manager.get_evaluation_criteria(
            role_type=role_type,
            text_content=resume_text,
            target_job_title=target_job_title,
        )
        return system_message, user_prompt

    @staticmethod
    def _sanitise_payload(payload: dict) -> dict:
        if "key_strengths" in payload and isinstance(payload["key_strengths"], list):
            payload["key_strengths"] = payload["key_strengths"][:5]
        if "areas_for_improvement" in payload and isinstance(payload["areas_for_improvement"], list):
            payload["areas_for_improvement"] = payload["areas_for_improvement"][:3]
        return payload

    def evaluate_resume(self, resume_text: str) -> EvaluationData:
        system_message, user_prompt = self._build_prompt(
            resume_text=resume_text,
            role_type=DEFAULT_ROLE,
        )
        payload = self._call_llm_with_retry(
            user_prompt=user_prompt,
            system_message=system_message,
            response_schema=EvaluationData.model_json_schema(),
        )
        payload = self._sanitise_payload(payload)
        return EvaluationData(**payload)

    def evaluate_resume_sg(
        self,
        resume_text: str,
        role_type: str,
        target_job_title: str = "",
    ) -> GenericSGEvaluation:
        if not is_sg_role(role_type):
            raise ValueError("Unsupported SG role type: " + role_type)

        system_message, user_prompt = self._build_prompt(
            resume_text=resume_text,
            role_type=role_type,
            target_job_title=target_job_title,
        )
        payload = self._call_llm_with_retry(
            user_prompt=user_prompt,
            system_message=system_message,
            response_schema=None,
        )
        payload = self._sanitise_payload(payload)
        evaluation = GenericSGEvaluation(**payload)
        assert_sg_categories(evaluation, role_type)
        return evaluation

    def evaluate(
        self,
        resume_text: str,
        role_type: str = DEFAULT_ROLE,
        target_job_title: str = "",
    ) -> EvaluationData | GenericSGEvaluation:
        try:
            if is_sg_role(role_type):
                return self.evaluate_resume_sg(
                    resume_text=resume_text,
                    role_type=role_type,
                    target_job_title=target_job_title,
                )
            return self.evaluate_resume(resume_text)
        except Exception as exc:
            logger.error("Error evaluating resume for role '%s': %s", role_type, exc)
            raise

