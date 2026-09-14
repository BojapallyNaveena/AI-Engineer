import os
import logging
from typing import Optional
from .base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    """Second fallback LLM provider using DeepSeek API via OpenAI SDK."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model_name = model_name
        self._client = None

    @property
    def name(self) -> str:
        return "deepseek"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _get_client(self):
        if self._client is None:
            if not self.is_available:
                raise ValueError("DEEPSEEK_API_KEY environment variable is not configured.")
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
        return self._client

    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        client = self._get_client()
        logger.info(f"Generating LLM extraction via DeepSeek fallback ({self.model_name})...")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=self.model_name,
            messages=messages,
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content or ""
        return ""
