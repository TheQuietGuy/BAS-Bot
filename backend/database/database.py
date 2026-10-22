"""Database engine and session helpers."""
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend import config
from backend.database.models import Base

os.makedirs(os.path.dirname(config.DATABASE_PATH) or ".", exist_ok=True)

engine = create_engine(f"sqlite:///{config.DATABASE_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
    """Context manager that yields a session and always closes it.

    Usage:
        with get_session() as session:
            session.add(obj)
            session.commit()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
