"""Base repository for common CRUD operations"""

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from web.models.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic base repository providing common CRUD operations.

    Type parameter T should be a SQLAlchemy model class.
    """

    def __init__(self, session: AsyncSession, model_class: type[T]) -> None:
        """
        Initialize repository.

        Args:
            session: SQLAlchemy async session
            model_class: Model class this repository manages
        """
        self._session = session
        self._model_class = model_class

    async def get(self, id: str | int) -> T | None:
        """
        Get entity by primary key.

        Args:
            id: Primary key value

        Returns:
            Entity if found, None otherwise
        """
        return await self._session.get(self._model_class, id)

    async def add(self, entity: T) -> T:
        """
        Add new entity to the session.

        Args:
            entity: Entity to add

        Returns:
            The added entity
        """
        self._session.add(entity)
        return entity

    async def delete(self, entity: T) -> None:
        """
        Delete entity from the session.

        Args:
            entity: Entity to delete
        """
        await self._session.delete(entity)

    async def list_all(self) -> list[T]:
        """
        Get all entities of this type.

        Returns:
            List of all entities
        """
        result = await self._session.execute(select(self._model_class))
        return list(result.scalars().all())
