import unittest
from src.validation.validators import RecordValidator, ValidationError


class TestRecordValidator(unittest.TestCase):
    def test_validate_research_paper_valid(self):
        paper = {
            "recordType": "RESEARCH_PAPER",
            "paper_url": "https://arxiv.org/abs/1706.03762",
            "github_url": "https://github.com/tensorflow/tensor2tensor",
            "github_stars": 42000,
        }
        self.assertTrue(RecordValidator.validate_research_paper(paper))

    def test_validate_research_paper_invalid_url(self):
        paper = {
            "recordType": "RESEARCH_PAPER",
            "paper_url": "not-a-valid-url",
        }
        with self.assertRaises(ValidationError):
            RecordValidator.validate_research_paper(paper)

    def test_validate_product_pricing_enum(self):
        # Valid pricing models
        for valid_model in ["FREE", "FREEMIUM", "PAID", "ENTERPRISE", None]:
            prod = {
                "recordType": "PRODUCT",
                "source": {"url": "https://example.com/product"},
                "content": {"startupName": "Test Startup", "pricingModel": valid_model},
            }
            self.assertTrue(RecordValidator.validate_product(prod))

        # Invalid pricing model
        invalid_prod = {
            "recordType": "PRODUCT",
            "source": {"url": "https://example.com/product"},
            "content": {"startupName": "Test Startup", "pricingModel": "SUPER_CHEAP"},
        }
        with self.assertRaises(ValidationError):
            RecordValidator.validate_product(invalid_prod)

    def test_validate_startup_missing_name(self):
        startup = {
            "recordType": "STARTUP",
            "source": {"url": "https://example.com/startup"},
            "content": {"entityName": ""},
        }
        with self.assertRaises(ValidationError):
            RecordValidator.validate_startup(startup)


if __name__ == "__main__":
    unittest.main()
