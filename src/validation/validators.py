import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

ALLOWED_PRICING_MODELS = {"FREE", "FREEMIUM", "PAID", "ENTERPRISE", None}
ALLOWED_RECORD_TYPES = {"RESEARCH_PAPER", "STARTUP", "PRODUCT", "JOB", "NEWS"}
URL_REGEX = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)


class ValidationError(Exception):
    """Custom exception raised when record validation fails."""
    pass


class RecordValidator:
    """Validator for verifying extracted entity schema integrity before storage."""

    @staticmethod
    def validate_url(url: Optional[str], field_name: str = "url") -> bool:
        if not url or not isinstance(url, str):
            raise ValidationError(f"Invalid or missing URL for field '{field_name}': {url}")
        if not URL_REGEX.match(url.strip()):
            raise ValidationError(f"Malformed URL string for field '{field_name}': {url}")
        return True

    @staticmethod
    def validate_pricing_model(pricing_model: Optional[str]) -> bool:
        if pricing_model is not None:
            upper_model = pricing_model.upper()
            if upper_model not in ALLOWED_PRICING_MODELS:
                raise ValidationError(
                    f"Invalid pricing model '{pricing_model}'. Must be one of: FREE, FREEMIUM, PAID, ENTERPRISE, or null."
                )
        return True

    @classmethod
    def validate_research_paper(cls, paper_dict: Dict[str, Any]) -> bool:
        if not isinstance(paper_dict, dict):
            raise ValidationError("Paper record must be a dictionary.")

        if paper_dict.get("recordType") != "RESEARCH_PAPER":
            raise ValidationError(f"Invalid recordType for paper: {paper_dict.get('recordType')}")

        cls.validate_url(paper_dict.get("paper_url"), "paper_url")

        if paper_dict.get("github_url"):
            cls.validate_url(paper_dict["github_url"], "github_url")

        stars = paper_dict.get("github_stars")
        if stars is not None and (not isinstance(stars, int) or stars < 0):
            raise ValidationError(f"Invalid github_stars value '{stars}'. Must be non-negative integer or null.")

        return True

    @classmethod
    def validate_startup(cls, startup_dict: Dict[str, Any]) -> bool:
        if not isinstance(startup_dict, dict):
            raise ValidationError("Startup record must be a dictionary.")

        if startup_dict.get("recordType") != "STARTUP":
            raise ValidationError(f"Invalid recordType for startup: {startup_dict.get('recordType')}")

        source = startup_dict.get("source", {})
        cls.validate_url(source.get("url"), "source.url")

        content = startup_dict.get("content", {})
        if not content.get("entityName"):
            raise ValidationError("Startup record missing required content.entityName.")

        emp_count = content.get("data", {}).get("employeeCount")
        if emp_count is not None and (not isinstance(emp_count, int) or emp_count < 0):
            raise ValidationError(f"Invalid employeeCount '{emp_count}'. Must be non-negative integer or null.")

        return True

    @classmethod
    def validate_product(cls, product_dict: Dict[str, Any]) -> bool:
        if not isinstance(product_dict, dict):
            raise ValidationError("Product record must be a dictionary.")

        if product_dict.get("recordType") != "PRODUCT":
            raise ValidationError(f"Invalid recordType for product: {product_dict.get('recordType')}")

        source = product_dict.get("source", {})
        cls.validate_url(source.get("url"), "source.url")

        content = product_dict.get("content", {})
        if not content.get("startupName"):
            raise ValidationError("Product record missing required content.startupName.")

        cls.validate_pricing_model(content.get("pricingModel"))
        return True

    @classmethod
    def validate_job(cls, job_dict: Dict[str, Any]) -> bool:
        if not isinstance(job_dict, dict):
            raise ValidationError("Job record must be a dictionary.")

        if job_dict.get("recordType") != "JOB":
            raise ValidationError(f"Invalid recordType for job: {job_dict.get('recordType')}")

        source = job_dict.get("source", {})
        cls.validate_url(source.get("url"), "source.url")

        return True

    @classmethod
    def validate_news(cls, news_dict: Dict[str, Any]) -> bool:
        if not isinstance(news_dict, dict):
            raise ValidationError("News record must be a dictionary.")

        if news_dict.get("recordType") != "NEWS":
            raise ValidationError(f"Invalid recordType for news: {news_dict.get('recordType')}")

        source = news_dict.get("source", {})
        cls.validate_url(source.get("url"), "source.url")

        return True
