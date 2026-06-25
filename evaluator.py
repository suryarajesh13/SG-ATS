from __future__ import annotations

import ast
import json
import logging
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


def _parse_llm_json(response_text: str) -> dict:
    """
    Robustly parse LLM output as JSON.
    Handles:
      - Proper JSON with double quotes
      - Python-style dicts with single quotes
      - Extra text before/after the JSON block
      - Trailing commas
    """
    response_text = response_text.strip()

    # Extract the outermost {...} block
    json_start = response_text.find("{")
    json_end = response_text.rfind("}")
    if json_start != -1 and json_end != -1:
        response_text = response_text[json_start:json_end + 1]

    # Attempt 1: strict JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.debug("json.loads failed (%s), trying fallbacks...", e)

    # Attempt 2: remove trailing commas before } or ] then retry
    import re
    cleaned = re.sub(r",\s*([}\]])", r"", response_text)
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

    # All attempts failed
    logger.error("Could not parse LLM response as JSON. Raw output:")
    logger.error(response_text)
    raise ValueError(
        "LLM did not return valid JSON. Raw output logged above. "
        "Try a different model or check your prompt templates."
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
        if response_schema is not None:
            kwargs["format"] = response_schema

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
        response_text = self._call_llm(
            user_prompt=user_prompt,
            system_message=system_message,
            response_schema=EvaluationData.model_json_schema(),
        )
        response_text = extract_json_from_response(response_text)
        payload = self._sanitise_payload(_parse_llm_json(response_text))
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
        response_text = self._call_llm(
            user_prompt=user_prompt,
            system_message=system_message,
            response_schema=None,
        )
        response_text = extract_json_from_response(response_text)
        payload = self._sanitise_payload(_parse_llm_json(response_text))
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

