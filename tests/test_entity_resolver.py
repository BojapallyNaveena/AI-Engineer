import unittest
from src.resolver.entity_resolver import EntityResolver, normalize_entity_name


class TestEntityResolver(unittest.TestCase):
    def test_normalize_entity_name(self):
        self.assertEqual(normalize_entity_name("OpenAI, Inc."), "openai")
        self.assertEqual(normalize_entity_name("Google LLC"), "google")
        self.assertEqual(normalize_entity_name("Anthropic Corp."), "anthropic")
        self.assertEqual(normalize_entity_name("Mistral AI GmbH"), "mistral ai")

    def test_resolve_alias(self):
        resolver = EntityResolver()
        res = resolver.resolve("Open AI", entity_type="STARTUP", known_canonical_names=["OpenAI"])
        self.assertEqual(res.canonical_name, "OpenAI")
        self.assertEqual(res.resolution_method, "alias")
        self.assertEqual(res.confidence, 1.0)

    def test_resolve_normalized(self):
        resolver = EntityResolver()
        res = resolver.resolve("Cohere Inc.", entity_type="STARTUP", known_canonical_names=["Cohere"])
        self.assertEqual(res.canonical_name, "Cohere")
        self.assertEqual(res.resolution_method, "normalized")
        self.assertEqual(res.confidence, 1.0)

    def test_resolve_fuzzy(self):
        resolver = EntityResolver(fuzzy_threshold=0.8)
        res = resolver.resolve("StabilityAI", entity_type="STARTUP", known_canonical_names=["Stability AI"])
        self.assertEqual(res.canonical_name, "Stability AI")
        self.assertEqual(res.resolution_method, "fuzzy")
        self.assertGreaterEqual(res.confidence, 0.8)

    def test_low_confidence_unresolved(self):
        resolver = EntityResolver(fuzzy_threshold=0.85)
        # Completely different entity name
        res = resolver.resolve("Totally Unrelated Corp", entity_type="STARTUP", known_canonical_names=["OpenAI"])
        self.assertEqual(res.canonical_name, "Totally Unrelated Corp")
        self.assertEqual(res.resolution_method, "unresolved")


if __name__ == "__main__":
    unittest.main()
