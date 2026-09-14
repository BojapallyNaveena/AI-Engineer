import os
import logging
from typing import Optional
from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Primary LLM provider using Google Gemini official SDK."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self._client = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _get_client(self):
        if self._client is None:
            if not self.is_available:
                raise ValueError("GEMINI_API_KEY environment variable is not configured.")
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        client = self._get_client()
        logger.info(f"Generating LLM extraction via Gemini ({self.model_name})...")

        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction

        response = await client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config if config else None,
        )
        return response.text or ""
