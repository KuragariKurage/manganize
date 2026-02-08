"""GenerationHistory model for manga generation tracking"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import JSON, ForeignKey, Index, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from manganize_web.models.database import Base


class GenerationTypeEnum(str, Enum):
    """Generation type for initial image or revision image"""

    INITIAL = "initial"
    REVISION = "revision"


class GenerationStatusEnum(str, Enum):
    """Valid status values for manga generation"""

    PENDING = "pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"


class GenerationHistory(Base):
    """
    Represents a manga generation request and its result.

    Tracks the input topic, generated title, character used, image data,
    status, and timestamps for each generation.
    """

    __tablename__ = "generation_history"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Generation inputs
    character_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_topic: Mapped[str] = mapped_column(Text, nullable=False)

    # Generation outputs
    generated_title: Mapped[str] = mapped_column(String(100), nullable=False)
    image_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    generation_type: Mapped[GenerationTypeEnum] = mapped_column(
        SQLEnum(GenerationTypeEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=GenerationTypeEnum.INITIAL,
    )
    parent_generation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("generation_history.id", ondelete="SET NULL"),
        nullable=True,
    )
    revision_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Status tracking
    status: Mapped[GenerationStatusEnum] = mapped_column(
        SQLEnum(GenerationStatusEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=GenerationStatusEnum.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Indexes for query performance
    __table_args__ = (
        Index("idx_created_at", "created_at"),
        Index("idx_status", "status"),
        Index("idx_generation_type", "generation_type"),
        Index("idx_parent_generation_id", "parent_generation_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<GenerationHistory(id={self.id}, "
            f"topic={self.input_topic[:30]}..., "
            f"type={self.generation_type}, "
            f"status={self.status})>"
        )
