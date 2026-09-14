import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from src.llm.base_provider import clean_json_text, BaseLLMProvider
from src.llm.orchestrator import LLMOrchestrator


class MockProvider(BaseLLMProvider):
    def __init__(self, provider_name: str, available: bool = True, should_fail: bool = False, return_json: dict = None):
        self._name = provider_name
        self._available = available
        self.should_fail = should_fail
        self.return_json = return_json or {"status": "ok"}

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        if self.should_fail:
            raise RuntimeError(f"Mock failure in {self._name}")
        import json
        return json.dumps(self.return_json)


class TestLLMOrchestrator(unittest.IsolatedAsyncioTestCase):
    def test_clean_json_text(self):
        raw_markdown = "```json\n{\"entityName\": \"OpenAI\"}\n```"
        self.assertEqual(clean_json_text(raw_markdown), "{\"entityName\": \"OpenAI\"}")
        
        plain_json = "{\"entityName\": \"Anthropic\"}"
        self.assertEqual(clean_json_text(plain_json), "{\"entityName\": \"Anthropic\"}")

    async def test_primary_provider_success(self):
        gemini = MockProvider("gemini", return_json={"startupName": "Mistral AI"})
        groq = MockProvider("groq", return_json={"startupName": "Groq Failover"})
        deepseek = MockProvider("deepseek", return_json={"startupName": "DeepSeek Failover"})

        orchestrator = LLMOrchestrator(providers=[gemini, groq, deepseek])
        data, provider_used = await orchestrator.extract_entity_json("Extract startup name")

        self.assertEqual(provider_used, "gemini")
        self.assertEqual(data["startupName"], "Mistral AI")

    async def test_fallback_to_groq_when_gemini_fails(self):
        gemini = MockProvider("gemini", should_fail=True)
        groq = MockProvider("groq", return_json={"startupName": "Cohere"})
        deepseek = MockProvider("deepseek", return_json={"startupName": "DeepSeek"})

        orchestrator = LLMOrchestrator(providers=[gemini, groq, deepseek])
        data, provider_used = await orchestrator.extract_entity_json("Extract startup name")

        self.assertEqual(provider_used, "groq")
        self.assertEqual(data["startupName"], "Cohere")

    async def test_fallback_to_deepseek_when_gemini_and_groq_fail(self):
        gemini = MockProvider("gemini", should_fail=True)
        groq = MockProvider("groq", should_fail=True)
        deepseek = MockProvider("deepseek", return_json={"startupName": "Perplexity AI"})

        orchestrator = LLMOrchestrator(providers=[gemini, groq, deepseek])
        data, provider_used = await orchestrator.extract_entity_json("Extract startup name")

        self.assertEqual(provider_used, "deepseek")
        self.assertEqual(data["startupName"], "Perplexity AI")

    async def test_all_providers_fail_raises_runtime_error(self):
        gemini = MockProvider("gemini", should_fail=True)
        groq = MockProvider("groq", should_fail=True)
        deepseek = MockProvider("deepseek", should_fail=True)

        orchestrator = LLMOrchestrator(providers=[gemini, groq, deepseek])
        with self.assertRaises(RuntimeError):
            await orchestrator.extract_entity_json("Extract data")


if __name__ == "__main__":
    unittest.main()
