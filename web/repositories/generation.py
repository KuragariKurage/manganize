"""Repository for GenerationHistory model"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from web.models.generation import GenerationHistory, GenerationStatusEnum
from web.repositories.base import BaseRepository


class GenerationRepository(BaseRepository[GenerationHistory]):
    """Repository for manga generation history data access"""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize generation repository.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, GenerationHistory)

    async def get_by_id(self, generation_id: str) -> GenerationHistory | None:
        """
        Get generation by ID.

        Args:
            generation_id: UUID of the generation

        Returns:
            GenerationHistory if found, None otherwise
        """
        return await self.get(generation_id)

    async def create(self, generation: GenerationHistory) -> GenerationHistory:
        """
        Create new generation record.

        Args:
            generation: Generation entity to create

        Returns:
            The created generation
        """
        return await self.add(generation)

    async def update_with_result(
        self,
        generation_id: str,
        image_data: bytes,
        title: str,
    ) -> None:
        """
        Update generation with successful result.

        Args:
            generation_id: UUID of the generation
            image_data: Generated image binary data
            title: Generated title
        """
        generation = await self.get_by_id(generation_id)
        if generation:
            generation.image_data = image_data
            generation.generated_title = title
            generation.status = GenerationStatusEnum.COMPLETED
            generation.completed_at = datetime.now(timezone.utc)

    async def update_error(
        self,
        generation_id: str,
        error_message: str,
    ) -> None:
        """
        Update generation with error status.

        Args:
            generation_id: UUID of the generation
            error_message: Error message to store
        """
        generation = await self.get_by_id(generation_id)
        if generation:
            generation.status = GenerationStatusEnum.ERROR
            generation.error_message = error_message
            generation.completed_at = datetime.now(timezone.utc)
