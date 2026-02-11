"""Repository for UploadSource model."""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from manganize_web.models.upload_source import UploadSource
from manganize_web.repositories.base import BaseRepository


class UploadSourceRepository(BaseRepository[UploadSource]):
    """Repository for uploaded source metadata."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UploadSource)

    async def get_by_id(self, upload_id: str) -> UploadSource | None:
        """Get upload source metadata by ID."""
        return await self.get(upload_id)

    async def create(self, source: UploadSource) -> UploadSource:
        """Create upload source metadata."""
        return await self.add(source)

    async def mark_used(self, upload_id: str) -> None:
        """Set used timestamp for an upload source."""
        source = await self.get_by_id(upload_id)
        if source:
            source.used_at = datetime.now(timezone.utc)
