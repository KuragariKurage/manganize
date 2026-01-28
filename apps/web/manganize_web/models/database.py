"""Database connection and session management"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from fastapi import Request
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from manganize_web.config import settings

if TYPE_CHECKING:
    from manganize_web.repositories.database_session import DatabaseSession


def create_engine() -> AsyncEngine:
    """
    Create async database engine.

    Returns:
        AsyncEngine: SQLAlchemy async engine instance
    """
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        future=True,
    )


def create_session_maker(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """
    Create async session maker from engine.

    Args:
        engine: SQLAlchemy async engine

    Returns:
        async_sessionmaker: Session factory
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# Base model class
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""

    metadata = MetaData()


async def get_db_session(request: Request) -> AsyncGenerator["DatabaseSession", Any]:
    """
    Dependency that provides DatabaseSession (Unit of Work).

    Args:
        request: FastAPI request object (automatically injected)

    Yields:
        DatabaseSession: Database session with repositories
    """
    # Lazy import to avoid circular dependency
    from manganize_web.repositories.database_session import DatabaseSession

    session_maker = request.app.state.session_maker

    async with session_maker() as session:
        db_session = DatabaseSession(session)
        try:
            yield db_session
        finally:
            await db_session.close()


async def init_db(engine: AsyncEngine) -> None:
    """
    Initialize database tables.

    Args:
        engine: SQLAlchemy async engine
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
