from __future__ import annotations

import logging
from typing import Any

from models import ModelProvider
from prompt import GEMINI_API_KEY, MODEL_PROVIDER_MAPPING
from providers import GeminiProvider, OllamaProvider

logger = logging.getLogger(__name__)


def extract_json_from_response(response_text: str) -> str:
    response_text = response_text.strip()

    if "<think>" in response_text:
        think_start = response_text.find("<think>")
        think_end = response_text.find("</think>")
        if think_start != -1 and think_end != -1:
            response_text = (
                response_text[:think_start] + response_text[think_end + 8:]
            )

    if response_text.startswith("```json"):
        response_text = response_text[7:]
    elif response_text.startswith("```"):
        response_text = response_text[3:]

    if response_text.endswith("```"):
        response_text = response_text[:-3]

    return response_text.strip()


def initialize_llm_provider(model_name: str) -> Any:
    model_provider = MODEL_PROVIDER_MAPPING.get(model_name, ModelProvider.OLLAMA)

    if model_provider == ModelProvider.GEMINI:
        if not GEMINI_API_KEY:
            logger.warning(
                "Gemini API key not found — falling back to Ollama for model %s.",
                model_name,
            )
            return OllamaProvider()
        logger.info("Using Google Gemini provider with model %s.", model_name)
        return GeminiProvider(api_key=GEMINI_API_KEY)

    logger.info("Using Ollama provider with model %s.", model_name)
    return OllamaProvider()
