"""Database connection and session management"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from web.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base model class
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""

    metadata = MetaData()


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """
    Dependency that provides database session.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator["DatabaseSession", Any]:
    """
    Dependency that provides DatabaseSession (Unit of Work).

    Yields:
        DatabaseSession: Database session with repositories
    """
    # Lazy import to avoid circular dependency
    from web.repositories.database_session import DatabaseSession

    async with async_session_maker() as session:
        db_session = DatabaseSession(session)
        try:
            yield db_session
        finally:
            await db_session.close()


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
