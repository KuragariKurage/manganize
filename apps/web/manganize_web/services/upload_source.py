"""Service for uploaded source document handling."""

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile

from manganize_web.config import settings
from manganize_web.models.upload_source import UploadSource
from manganize_web.repositories.database_session import DatabaseSession
from manganize_web.services.storage import generate_presigned_get_url, upload_object
from manganize_web.utils.file_processing import read_validated_file_bytes


class UploadSourceService:
    """Service that stores upload metadata and object storage references."""

    @staticmethod
    def _normalize_utc(dt: datetime) -> datetime:
        """
        Normalize datetime to UTC-aware.

        SQLite can return naive datetimes even when UTC values were stored.
        """
        if dt.tzinfo is None or dt.utcoffset() is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    async def create_upload(
        self,
        file: UploadFile,
        db_session: DatabaseSession,
    ) -> UploadSource:
        """
        Store uploaded file in object storage and persist metadata.

        Args:
            file: Uploaded file
            db_session: Database session

        Returns:
            Created upload metadata
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイル名が不正です")

        content = await read_validated_file_bytes(file)
        upload_id = str(uuid.uuid4())

        suffix = Path(file.filename).suffix.lower()
        now = datetime.now(timezone.utc)
        object_key = (
            f"{settings.storage_object_prefix}/{now:%Y/%m/%d}/{upload_id}{suffix}"
        )

        try:
            await upload_object(
                object_key=object_key,
                data=content,
                content_type=file.content_type,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"オブジェクトストレージへの保存に失敗しました: {str(e)}",
            )

        source = UploadSource(
            id=upload_id,
            object_key=object_key,
            original_filename=file.filename,
            content_type=file.content_type,
            file_size=len(content),
            created_at=now,
            expires_at=now + timedelta(hours=settings.upload_ttl_hours),
        )
        await db_session.upload_sources.create(source)
        await db_session.commit()
        return source

    async def resolve_signed_url(
        self,
        upload_id: str,
        db_session: DatabaseSession,
    ) -> str:
        """
        Resolve upload ID to a presigned download URL.

        Args:
            upload_id: Upload source ID
            db_session: Database session

        Returns:
            Presigned URL
        """
        source = await db_session.upload_sources.get_by_id(upload_id)
        if not source:
            raise ValueError("Upload source not found")

        now = datetime.now(timezone.utc)
        expires_at = self._normalize_utc(source.expires_at)
        if expires_at <= now:
            raise ValueError("Upload source has expired")

        signed_url = await generate_presigned_get_url(
            object_key=source.object_key,
            expires_in=settings.storage_signed_url_ttl_seconds,
        )
        await db_session.upload_sources.mark_used(upload_id)
        await db_session.commit()
        return signed_url

    async def ensure_upload_available(
        self,
        upload_id: str,
        db_session: DatabaseSession,
    ) -> None:
        """
        Validate that upload metadata exists and is not expired.

        Args:
            upload_id: Upload source ID
            db_session: Database session
        """
        source = await db_session.upload_sources.get_by_id(upload_id)
        if not source:
            raise ValueError("Upload source not found")

        expires_at = self._normalize_utc(source.expires_at)
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("Upload source has expired")


upload_source_service = UploadSourceService()
