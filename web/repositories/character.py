"""Repository for Character model"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from web.models.character import Character
from web.repositories.base import BaseRepository


class CharacterRepository(BaseRepository[Character]):
    """Repository for character data access"""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize character repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Character)

    async def get_by_name(self, name: str) -> Character | None:
        """
        Get character by name.

        Args:
            name: Character name (primary key)

        Returns:
            Character if found, None otherwise
        """
        return await self.get(name)

    async def get_default(self) -> Character | None:
        """
        Get the default character.

        Returns:
            Default character if exists, None otherwise
        """
        result = await self._session.execute(
            select(Character).where(Character.is_default == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Character]:
        """
        Get all characters.

        Returns:
            List of all characters
        """
        return await super().list_all()
