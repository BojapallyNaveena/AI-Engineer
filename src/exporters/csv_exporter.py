import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
from sqlalchemy.orm import Session
from src.storage.database import get_session
from src.storage.models import (
    ResearchPaperModel,
    StartupModel,
    ProductModel,
    JobModel,
    NewsModel,
    EntityMappingModel,
)

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exporter for generating CSV artifacts for all system entities using pandas."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def export_all(self, export_dir: str = "data/exports") -> Dict[str, str]:
        """
        Query database records for all entities and write CSV files to export_dir.
        
        Returns:
            Dict[str, str]: Mapping of entity name to output CSV file path.
        """
        target_path = Path(export_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        session = self._session if self._session else get_session()
        try:
            exported_files = {
                "research_papers": self._export_research_papers(session, target_path / "research_papers.csv"),
                "startups": self._export_startups(session, target_path / "startups.csv"),
                "products": self._export_products(session, target_path / "products.csv"),
                "jobs": self._export_jobs(session, target_path / "jobs.csv"),
                "news": self._export_news(session, target_path / "news.csv"),
                "entity_mappings": self._export_entity_mappings(session, target_path / "entity_mappings.csv"),
            }
            logger.info(f"Successfully generated CSV exports in '{export_dir}'")
            return exported_files
        finally:
            if not self._session:
                session.close()

    def _export_research_papers(self, session: Session, filepath: Path) -> str:
        records = session.query(ResearchPaperModel).all()
        data = [
            {
                "id": r.id,
                "schemaVersion": r.schema_version,
                "recordType": r.record_type,
                "title": r.title,
                "authors": ", ".join(r.authors) if r.authors else "",
                "paper_url": r.paper_url,
                "github_url": r.github_url,
                "github_stars": r.github_stars,
                "published_date": r.published_date,
                "collected_at": r.collected_at.isoformat() if r.collected_at else "",
            }
            for r in records
        ]
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)

    def _export_startups(self, session: Session, filepath: Path) -> str:
        records = session.query(StartupModel).all()
        data = [
            {
                "id": r.id,
                "schemaVersion": r.schema_version,
                "recordType": r.record_type,
                "entityName": r.entity_name,
                "sourceName": r.source_name,
                "sourceUrl": r.source_url,
                "employeeCount": r.employee_count,
                "collectedAt": r.collected_at.isoformat() if r.collected_at else "",
            }
            for r in records
        ]
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)

    def _export_products(self, session: Session, filepath: Path) -> str:
        records = session.query(ProductModel).all()
        data = [
            {
                "id": r.id,
                "schemaVersion": r.schema_version,
                "recordType": r.record_type,
                "startupName": r.startup_name,
                "sourceName": r.source_name,
                "sourceUrl": r.source_url,
                "pricingModel": r.pricing_model,
                "collectedAt": r.collected_at.isoformat() if r.collected_at else "",
            }
            for r in records
        ]
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)

    def _export_jobs(self, session: Session, filepath: Path) -> str:
        records = session.query(JobModel).all()
        data = [
            {
                "id": r.id,
                "schemaVersion": r.schema_version,
                "recordType": r.record_type,
                "companyName": r.company_name,
                "title": r.title,
                "sourceName": r.source_name,
                "sourceUrl": r.source_url,
                "publishedDate": r.published_date,
                "isFresh": r.is_fresh,
                "collectedAt": r.collected_at.isoformat() if r.collected_at else "",
            }
            for r in records
        ]
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)

    def _export_news(self, session: Session, filepath: Path) -> str:
        records = session.query(NewsModel).all()
        data = [
            {
                "id": r.id,
                "schemaVersion": r.schema_version,
                "recordType": r.record_type,
                "title": r.title,
                "contentSummary": r.content_summary,
                "sourceName": r.source_name,
                "sourceUrl": r.source_url,
                "publishedDate": r.published_date,
                "isFresh": r.is_fresh,
                "collectedAt": r.collected_at.isoformat() if r.collected_at else "",
            }
            for r in records
        ]
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)

    def _export_entity_mappings(self, session: Session, filepath: Path) -> str:
        records = session.query(EntityMappingModel).all()
        data = [
            {
                "id": r.id,
                "rawName": r.raw_name,
                "canonicalName": r.canonical_name,
                "entityType": r.entity_type,
                "sourceUrl": r.source_url,
                "resolutionMethod": r.resolution_method,
                "confidence": r.confidence,
                "createdAt": r.created_at.isoformat() if r.created_at else "",
            }
            for r in records
        ]
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        return str(filepath)
