"""Repository for GenerationHistory model"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from manganize_web.models.generation import (
    GenerationHistory,
    GenerationStatusEnum,
    GenerationTypeEnum,
)
from manganize_web.repositories.base import BaseRepository


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

    async def list_history(
        self,
        page: int = 1,
        limit: int = 10,
        status_filter: GenerationStatusEnum | None = None,
    ) -> tuple[list[GenerationHistory], int]:
        """
        List generation history with pagination and optional filtering.

        Args:
            page: Page number (1-indexed)
            limit: Number of items per page
            status_filter: Optional status to filter by

        Returns:
            Tuple of (list of generations, total count)
        """
        # Build base query
        query = select(GenerationHistory)

        # Apply status filter if provided
        if status_filter:
            query = query.where(GenerationHistory.status == status_filter)

        # Order by created_at DESC (newest first)
        query = query.order_by(GenerationHistory.created_at.desc())

        # Get total count
        count_query = select(GenerationHistory)
        if status_filter:
            count_query = count_query.where(GenerationHistory.status == status_filter)
        count_result = await self._session.execute(count_query)
        total_count = len(list(count_result.scalars().all()))

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await self._session.execute(query)
        generations = list(result.scalars().all())

        return generations, total_count

    async def delete_by_id(self, generation_id: str) -> bool:
        """
        Delete generation by ID.

        Args:
            generation_id: UUID of the generation to delete

        Returns:
            True if deleted, False if not found
        """
        generation = await self.get_by_id(generation_id)
        if generation:
            await self.delete(generation)
            return True
        return False

    async def create_revision(
        self,
        parent_generation: GenerationHistory,
        revision_generation_id: str,
        revision_payload: dict[str, Any],
    ) -> GenerationHistory:
        """
        Create revision generation record.

        Args:
            parent_generation: Parent generation to revise
            revision_generation_id: New generation ID for revision
            revision_payload: Revision request payload

        Returns:
            Created revision generation
        """
        revision = GenerationHistory(
            id=revision_generation_id,
            character_name=parent_generation.character_name,
            input_topic=parent_generation.input_topic,
            generated_title=parent_generation.generated_title,
            status=GenerationStatusEnum.PENDING,
            generation_type=GenerationTypeEnum.REVISION,
            parent_generation_id=parent_generation.id,
            revision_payload=revision_payload,
            created_at=datetime.now(timezone.utc),
        )
        return await self.create(revision)

    async def get_parent(self, generation_id: str) -> GenerationHistory | None:
        """
        Get parent generation of a revision.

        Args:
            generation_id: Revision generation ID

        Returns:
            Parent generation if exists, None otherwise
        """
        generation = await self.get_by_id(generation_id)
        if not generation or not generation.parent_generation_id:
            return None
        return await self.get_by_id(generation.parent_generation_id)

    async def list_revisions(
        self, parent_generation_id: str
    ) -> list[GenerationHistory]:
        """
        List revisions for a given parent generation.

        Args:
            parent_generation_id: Parent generation ID

        Returns:
            Revisions ordered by created_at ASC
        """
        query = (
            select(GenerationHistory)
            .where(GenerationHistory.parent_generation_id == parent_generation_id)
            .order_by(GenerationHistory.created_at.asc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
