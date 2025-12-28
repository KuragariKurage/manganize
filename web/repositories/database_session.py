"""DatabaseSession for transaction management and repository coordination"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from web.repositories.character import CharacterRepository
from web.repositories.generation import GenerationRepository


class DatabaseSession:
    """
    Database session manager that coordinates repositories and transactions.

    Implements the Unit of Work pattern by managing multiple repositories
    and providing transaction control (commit/rollback).

    Usage:
        async with get_db_session() as db_session:
            generation = await db_session.generations.get_by_id(gen_id)
            await db_session.commit()
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

        # Initialize repositories
        self.generations = GenerationRepository(session)
        self.characters = CharacterRepository(session)

    async def commit(self) -> None:
        """Commit the current transaction"""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction"""
        await self._session.rollback()

    async def close(self) -> None:
        """Close the database session"""
        await self._session.close()

    async def __aenter__(self) -> "DatabaseSession":
        """Enter async context manager"""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager with automatic rollback on error"""
        if exc_type:
            await self.rollback()
        await self.close()
