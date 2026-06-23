import os
from models import ModelProvider

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

MODEL_PARAMETERS = {
    "llama3": {"temperature": 0.1, "top_p": 0.9},
    "mistral": {"temperature": 0.1, "top_p": 0.9},
    "gemma3": {"temperature": 0.1, "top_p": 0.9},
    "deepseek-r1": {"temperature": 0.1, "top_p": 0.9},
    "gemini-1.5-flash": {"temperature": 0.1, "top_p": 0.9},
    "gemini-1.5-pro": {"temperature": 0.1, "top_p": 0.9},
}

MODEL_PROVIDER_MAPPING = {
    "gemini-1.5-flash": ModelProvider.GEMINI,
    "gemini-1.5-pro": ModelProvider.GEMINI,
}
