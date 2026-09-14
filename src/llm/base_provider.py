import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def clean_json_text(raw_text: str) -> str:
    """Strip markdown code block formatting (```json ... ```) from raw text."""
    if not raw_text:
        return ""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers (Gemini, Groq, DeepSeek)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier string."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if API key and configuration for this provider are present."""
        pass

    @abstractmethod
    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate raw text response from provider."""
        pass

    async def extract_json(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate response and parse as validated JSON object.
        Enforces JSON output contract.
        """
        json_instruction = (
            "IMPORTANT: Return ONLY a valid JSON object matching the requested schema. "
            "Do NOT include markdown formatting or explanation. "
            "If information is missing in the provided source text, set the field value to null. "
            "Do NOT guess or fabricate data."
        )
        combined_system = f"{system_instruction}\n{json_instruction}" if system_instruction else json_instruction

        raw_output = await self.generate_text(prompt, system_instruction=combined_system)
        cleaned = clean_json_text(raw_output)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(f"Provider {self.name} output invalid JSON: {exc}. Content: {cleaned[:200]}")
            raise ValueError(f"Failed to parse JSON response from {self.name}: {exc}") from exc
