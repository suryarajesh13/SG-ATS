from __future__ import annotations

import json
import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaProvider:
    def chat(
        self,
        model: str,
        messages: list,
        temperature: float = 0.1,
        top_p: float = 0.9,
        format: Optional[dict] = None,
        **kwargs,
    ) -> dict:
        payload: dict = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "top_p": top_p},
        }
        if format is not None:
            payload["format"] = format
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        return response.json()


class GeminiProvider:
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._genai = genai
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is required for Gemini support. "
                "Install it with: pip install google-generativeai"
            ) from exc

    def chat(
        self,
        model: str,
        messages: list,
        temperature: float = 0.1,
        top_p: float = 0.9,
        format: Optional[dict] = None,
        **kwargs,
    ) -> str:
        system_msg = next(
            (m["content"] for m in messages if m["role"] == "system"), ""
        )
        user_msg = next(
            (m["content"] for m in messages if m["role"] == "user"), ""
        )

        generation_config = self._genai.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
        )

        if format is not None:
            generation_config = self._genai.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                response_mime_type="application/json",
                response_schema=format,
            )

        gmodel = self._genai.GenerativeModel(
            model_name=model,
            system_instruction=system_msg,
            generation_config=generation_config,
        )
        response = gmodel.generate_content(user_msg)
        return response.text
