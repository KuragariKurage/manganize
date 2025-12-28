"""Character model for manga character definitions"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from web.models.database import Base


class Character(Base):
    """
    Represents a manga character with personality traits and speech style.

    Characters can be used in generation requests. The default character
    'kurage' is pre-seeded and cannot be deleted.

    Attributes:
        name: ASCII identifier (a-zA-Z0-9_)
        display_name: Display name (Japanese OK)
        nickname: Optional nickname
        attributes: List of character attributes
        personality: Base personality description
        speech_style: Speech patterns, tone, examples, forbidden patterns
        reference_images: Optional portrait and full_body image paths
        is_default: Whether this is the default character
    """

    __tablename__ = "characters"

    # Primary key
    name: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Character identity
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Character definition
    attributes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    speech_style: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Optional reference images (portrait, full_body)
    reference_images: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)

    # Metadata
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Character(name={self.name}, "
            f"display_name={self.display_name}, "
            f"is_default={self.is_default})>"
        )
