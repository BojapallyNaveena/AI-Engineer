import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None


def init_db(db_url: str = "sqlite:///data/app.db") -> Engine:
    """Initialize database engine and create tables."""
    global _engine, _SessionFactory

    if db_url.startswith("sqlite:///") and db_url != "sqlite:///:memory:":
        db_path_str = db_url.replace("sqlite:///", "")
        db_path = Path(db_path_str)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(db_url, echo=False, future=True)
    _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False)

    # Import models to ensure they are registered with Base before create_all
    from . import models  # noqa: F401
    Base.metadata.create_all(_engine)

    return _engine


def get_engine() -> Engine:
    """Get initialized database engine."""
    global _engine
    if _engine is None:
        return init_db()
    return _engine


def get_session() -> Session:
    """Get a new database ORM session."""
    global _SessionFactory
    if _SessionFactory is None:
        init_db()
    return _SessionFactory()
