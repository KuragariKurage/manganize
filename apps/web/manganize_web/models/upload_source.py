"""UploadSource model for user-uploaded documents stored in object storage."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from manganize_web.models.database import Base


class UploadSource(Base):
    """
    Represents an uploaded source document in private object storage.

    The application stores only metadata and object key in DB.
    File bytes are persisted in object storage (S3-compatible backend).
    """

    __tablename__ = "upload_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    __table_args__ = (
        Index("idx_upload_sources_created_at", "created_at"),
        Index("idx_upload_sources_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<UploadSource(id={self.id}, filename={self.original_filename}, "
            f"object_key={self.object_key})>"
        )
