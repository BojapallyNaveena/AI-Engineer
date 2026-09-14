import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, UniqueConstraint
from .database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    collected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ResearchPaperModel(Base):
    __tablename__ = "research_papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(50), default="1.0", nullable=False)
    record_type = Column(String(50), default="RESEARCH_PAPER", nullable=False)
    title = Column(String(1024), nullable=True)
    _authors_json = Column("authors", Text, nullable=True)
    paper_url = Column(String(2048), nullable=False, unique=True)
    github_url = Column(String(2048), nullable=True)
    github_stars = Column(Integer, nullable=True)
    published_date = Column(String(100), nullable=True)
    collected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    @property
    def authors(self) -> List[str]:
        if not self._authors_json:
            return []
        try:
            return json.loads(self._authors_json)
        except Exception:
            return []

    @authors.setter
    def authors(self, value: List[str]):
        self._authors_json = json.dumps(value or [])


class StartupModel(Base):
    __tablename__ = "startups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(50), default="1.0", nullable=False)
    record_type = Column(String(50), default="STARTUP", nullable=False)
    entity_name = Column(String(255), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_url = Column(String(2048), nullable=False)
    employee_count = Column(Integer, nullable=True)
    collected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(50), default="1.0", nullable=False)
    record_type = Column(String(50), default="PRODUCT", nullable=False)
    startup_name = Column(String(255), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_url = Column(String(2048), nullable=False)
    pricing_model = Column(String(50), nullable=True)
    collected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(50), default="1.0", nullable=False)
    record_type = Column(String(50), default="JOB", nullable=False)
    company_name = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_url = Column(String(2048), nullable=False, unique=True)
    published_date = Column(String(100), nullable=True)
    is_fresh = Column(Boolean, default=False, nullable=False)
    collected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class NewsModel(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(50), default="1.0", nullable=False)
    record_type = Column(String(50), default="NEWS", nullable=False)
    title = Column(String(1024), nullable=False)
    content_summary = Column(Text, nullable=True)
    source_name = Column(String(255), nullable=False)
    source_url = Column(String(2048), nullable=False, unique=True)
    published_date = Column(String(100), nullable=True)
    is_fresh = Column(Boolean, default=False, nullable=False)
    collected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class EntityMappingModel(Base):
    __tablename__ = "entity_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)
    source_url = Column(String(2048), nullable=True)
    resolution_method = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class CrawlJobModel(Base):
    __tablename__ = "crawl_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False)
    source_url = Column(String(2048), nullable=False)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
