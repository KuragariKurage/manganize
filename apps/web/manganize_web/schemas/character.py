"""Pydantic schemas for character management"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SpeechStyle(BaseModel):
    """Speech style configuration for a character"""

    tone: str = Field(
        ..., min_length=1, max_length=500, description="Voice tone description"
    )
    patterns: list[str] = Field(
        default_factory=list, description="Common speech patterns the character uses"
    )
    examples: list[str] = Field(
        default_factory=list, description="Example phrases the character would say"
    )
    forbidden: list[str] = Field(
        default_factory=list, description="Speech patterns the character should avoid"
    )


class CharacterCreate(BaseModel):
    """Request schema for creating a new character"""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="ASCII identifier (a-zA-Z0-9_)",
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    display_name: str = Field(
        ..., min_length=1, max_length=200, description="Display name (Japanese OK)"
    )
    nickname: str | None = Field(None, max_length=200, description="Optional nickname")
    attributes: list[str] = Field(
        ..., min_items=1, description="Character attributes (e.g., '技術オタク')"
    )
    personality: str = Field(
        ..., min_length=1, max_length=2000, description="Base personality description"
    )
    speech_style: SpeechStyle = Field(..., description="Speech patterns and tone")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name contains only ASCII alphanumeric and underscore"""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Name must contain only ASCII letters, numbers, and underscores"
            )
        return v


class CharacterUpdate(BaseModel):
    """Request schema for updating a character"""

    display_name: str | None = Field(None, min_length=1, max_length=200)
    nickname: str | None = Field(None, max_length=200)
    attributes: list[str] | None = Field(None, min_items=1)
    personality: str | None = Field(None, min_length=1, max_length=2000)
    speech_style: SpeechStyle | None = None


class CharacterResponse(BaseModel):
    """Response schema for character"""

    name: str
    display_name: str
    nickname: str | None
    attributes: list[str]
    personality: str
    speech_style: dict[str, list[str] | str]
    reference_images: dict[str, str] | None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CharacterListResponse(BaseModel):
    """Response schema for character list (simplified)"""

    name: str
    display_name: str
    nickname: str | None
    is_default: bool

    model_config = {"from_attributes": True}
