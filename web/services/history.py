"""Service layer for generation history management"""

from web.models.generation import GenerationHistory, GenerationStatusEnum
from web.repositories.database_session import DatabaseSession


class HistoryService:
    """Service for managing generation history"""

    async def list_history(
        self,
        db_session: DatabaseSession,
        page: int = 1,
        limit: int = 10,
        status_filter: GenerationStatusEnum | None = None,
    ) -> tuple[list[GenerationHistory], int]:
        """
        List generation history with pagination.

        Args:
            db_session: Database session
            page: Page number (1-indexed)
            limit: Number of items per page
            status_filter: Optional status to filter by

        Returns:
            Tuple of (list of generations, total count)
        """
        return await db_session.generations.list_history(
            page=page,
            limit=limit,
            status_filter=status_filter,
        )

    async def get_by_id(
        self,
        generation_id: str,
        db_session: DatabaseSession,
    ) -> GenerationHistory | None:
        """
        Get generation by ID.

        Args:
            generation_id: UUID of the generation
            db_session: Database session

        Returns:
            GenerationHistory if found, None otherwise
        """
        return await db_session.generations.get_by_id(generation_id)

    async def delete_by_id(
        self,
        generation_id: str,
        db_session: DatabaseSession,
    ) -> bool:
        """
        Delete generation by ID.

        Args:
            generation_id: UUID of the generation to delete
            db_session: Database session

        Returns:
            True if deleted, False if not found
        """
        deleted = await db_session.generations.delete_by_id(generation_id)
        if deleted:
            await db_session.commit()
        return deleted


# Global instance
history_service = HistoryService()
