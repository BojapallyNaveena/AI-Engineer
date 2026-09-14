import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from .database import get_session
from .models import (
    ResearchPaperModel,
    StartupModel,
    ProductModel,
    JobModel,
    NewsModel,
    EntityMappingModel,
    CrawlJobModel,
    SourceModel,
)

logger = logging.getLogger(__name__)


class Repository:
    """Data repository for persistent database operations with deduplication checks."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def _get_session(self) -> Session:
        return self._session if self._session else get_session()


    def insert_research_paper(self, paper_data: Dict[str, Any]) -> ResearchPaperModel:
        """Insert or update a research paper record."""
        session = self._session if self._session else get_session()
        try:
            url = paper_data["paper_url"]
            existing = session.query(ResearchPaperModel).filter_by(paper_url=url).first()
            if existing:
                logger.info(f"Duplicate paper URL detected in database: {url}. Updating record.")
                existing.title = paper_data.get("title") or existing.title
                existing.authors = paper_data.get("authors") or existing.authors
                existing.github_url = paper_data.get("github_url") or existing.github_url
                if paper_data.get("github_stars") is not None:
                    existing.github_stars = paper_data["github_stars"]
                existing.published_date = paper_data.get("published_date") or existing.published_date
                record = existing
            else:
                record = ResearchPaperModel(
                    schema_version=paper_data.get("schemaVersion", "1.0"),
                    record_type=paper_data.get("recordType", "RESEARCH_PAPER"),
                    title=paper_data.get("title"),
                    authors=paper_data.get("authors", []),
                    paper_url=url,
                    github_url=paper_data.get("github_url"),
                    github_stars=paper_data.get("github_stars"),
                    published_date=paper_data.get("published_date"),
                )
                session.add(record)

            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting research paper {paper_data.get('paper_url')}: {e}")
            raise
        finally:
            if not self._session:
                session.close()

    def get_research_paper_by_url(self, paper_url: str) -> Optional[ResearchPaperModel]:
        session = self._session if self._session else get_session()
        try:
            return session.query(ResearchPaperModel).filter_by(paper_url=paper_url).first()
        finally:
            if not self._session:
                session.close()

    def insert_startup(self, startup_data: Dict[str, Any]) -> StartupModel:
        session = self._session if self._session else get_session()
        try:
            record = StartupModel(
                schema_version=startup_data.get("schemaVersion", "1.0"),
                record_type=startup_data.get("recordType", "STARTUP"),
                entity_name=startup_data["content"]["entityName"],
                source_name=startup_data["source"]["name"],
                source_url=startup_data["source"]["url"],
                employee_count=startup_data["content"]["data"].get("employeeCount"),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting startup record: {e}")
            raise
        finally:
            if not self._session:
                session.close()

    def insert_product(self, product_data: Dict[str, Any]) -> ProductModel:
        session = self._session if self._session else get_session()
        try:
            record = ProductModel(
                schema_version=product_data.get("schemaVersion", "1.0"),
                record_type=product_data.get("recordType", "PRODUCT"),
                startup_name=product_data["content"]["startupName"],
                source_name=product_data["source"]["name"],
                source_url=product_data["source"]["url"],
                pricing_model=product_data["content"].get("pricingModel"),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting product record: {e}")
            raise
        finally:
            if not self._session:
                session.close()

    def insert_job(self, job_data: Dict[str, Any]) -> JobModel:
        session = self._session if self._session else get_session()
        try:
            url = job_data["source"]["url"]
            existing = session.query(JobModel).filter_by(source_url=url).first()
            if existing:
                logger.info(f"Duplicate job URL in DB: {url}. Updating.")
                existing.title = job_data.get("title", existing.title)
                existing.is_fresh = job_data.get("is_fresh", existing.is_fresh)
                record = existing
            else:
                record = JobModel(
                    schema_version=job_data.get("schemaVersion", "1.0"),
                    record_type=job_data.get("recordType", "JOB"),
                    company_name=job_data.get("company_name", "Unknown"),
                    title=job_data.get("title", "Unknown"),
                    source_name=job_data["source"]["name"],
                    source_url=url,
                    published_date=job_data.get("published_date"),
                    is_fresh=job_data.get("is_fresh", False),
                )
                session.add(record)

            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting job record: {e}")
            raise
        finally:
            if not self._session:
                session.close()

    def insert_news(self, news_data: Dict[str, Any]) -> NewsModel:
        session = self._session if self._session else get_session()
        try:
            url = news_data["source"]["url"]
            existing = session.query(NewsModel).filter_by(source_url=url).first()
            if existing:
                logger.info(f"Duplicate news URL in DB: {url}. Updating.")
                existing.title = news_data.get("title", existing.title)
                existing.is_fresh = news_data.get("is_fresh", existing.is_fresh)
                record = existing
            else:
                record = NewsModel(
                    schema_version=news_data.get("schemaVersion", "1.0"),
                    record_type=news_data.get("recordType", "NEWS"),
                    title=news_data.get("title", "Untitled"),
                    content_summary=news_data.get("content_summary"),
                    source_name=news_data["source"]["name"],
                    source_url=url,
                    published_date=news_data.get("published_date"),
                    is_fresh=news_data.get("is_fresh", False),
                )
                session.add(record)

            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting news record: {e}")
            raise
        finally:
            if not self._session:
                session.close()

    def insert_entity_mapping(self, mapping_data: Dict[str, Any]) -> EntityMappingModel:
        session = self._session if self._session else get_session()
        try:
            record = EntityMappingModel(
                raw_name=mapping_data["raw_name"],
                canonical_name=mapping_data["canonical_name"],
                entity_type=mapping_data["entity_type"],
                source_url=mapping_data.get("source_url"),
                resolution_method=mapping_data["resolution_method"],
                confidence=float(mapping_data["confidence"]),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting entity mapping: {e}")
            raise
        finally:
            if not self._session:
                session.close()
