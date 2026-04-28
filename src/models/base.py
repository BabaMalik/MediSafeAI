"""
Base Database Configuration
SQLAlchemy base class and database session management


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Create declarative base
Base = declarative_base()

# Database engine
_engine = None
_session_factory = None


def get_engine(database_url: str = None, **kwargs):
    """
    Get or create database engine

    Args:
        database_url: Database connection URL
        **kwargs: Additional engine arguments

    Returns:
        SQLAlchemy engine instance
    """
    global _engine

    if _engine is None:
        db_url = database_url or settings.DATABASE_URL

        engine_kwargs = {
            'pool_size': settings.DATABASE_POOL_SIZE,
            'max_overflow': settings.DATABASE_MAX_OVERFLOW,
            'echo': settings.DATABASE_ECHO,
            'pool_pre_ping': True,  # Verify connections before using
        }
        engine_kwargs.update(kwargs)

        logger.info(f"Creating database engine: {db_url.split('@')[-1]}")  # Log without credentials
        _engine = create_engine(db_url, **engine_kwargs)

    return _engine


def get_session_factory():
    """Get or create session factory"""
    global _session_factory

    if _session_factory is None:
        engine = get_engine()
        _session_factory = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
        )

    return _session_factory


def get_db_session() -> Session:
    """
    Get a database session

    Returns:
        SQLAlchemy session instance
    """
    return get_session_factory()()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    Automatically handles commit/rollback

    Yields:
        Database session

    Example:
        with get_db() as db:
            patient = db.query(Patient).first()
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_db(database_url: str = None):
    """
    Initialize database tables

    Args:
        database_url: Database connection URL
    """
    engine = get_engine(database_url)

    logger.info("Creating database tables...")

    # Import all models to ensure they're registered
    from src.models import patient, audit  # noqa: F401

    # Create all tables
    Base.metadata.create_all(bind=engine)

    logger.info("Database tables created successfully")


def drop_all_tables(database_url: str = None):
    """
    Drop all database tables (use with caution!)

    Args:
        database_url: Database connection URL
    """
    engine = get_engine(database_url)

    logger.warning("Dropping all database tables...")

    # Import all models
    from src.models import patient, audit  # noqa: F401

    # Drop all tables
    Base.metadata.drop_all(bind=engine)

    logger.info("All database tables dropped")


def reset_db(database_url: str = None):
    """
    Reset database (drop and recreate all tables)

    Args:
        database_url: Database connection URL
    """
    logger.warning("Resetting database...")
    drop_all_tables(database_url)
    init_db(database_url)
    logger.info("Database reset complete")
