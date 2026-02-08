"""Pydantic schemas for manga generation requests and responses"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from manganize_web.models.generation import GenerationStatusEnum, GenerationTypeEnum


class GenerationCreate(BaseModel):
    """Request schema for creating a new manga generation"""

    topic: str = Field(
        ..., min_length=1, max_length=10000, description="Topic to generate manga about"
    )
    character: str = Field(
        ..., min_length=1, max_length=100, description="Character name to use"
    )


class GenerationResponse(BaseModel):
    """Response schema for manga generation"""

    id: str
    character_name: str
    input_topic: str
    generated_title: str
    status: str
    generation_type: str
    parent_generation_id: str | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class GenerationStatus(BaseModel):
    """Schema for generation status updates via SSE"""

    id: str
    status: GenerationStatusEnum
    message: str
    progress: int = Field(..., ge=0, le=100, description="Progress of the generation")

    model_config = {"use_enum_values": True}


class RevisionTargetPoint(BaseModel):
    """Point target for pinpoint edit"""

    kind: Literal["point"]
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    radius: float = Field(default=0.04, gt=0.0, le=0.2)


class RevisionTargetBox(BaseModel):
    """Box target for area edit"""

    kind: Literal["box"]
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    w: float = Field(..., gt=0.0, le=1.0)
    h: float = Field(..., gt=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bounds(self) -> "RevisionTargetBox":
        """Validate that the box is inside normalized image bounds."""
        if self.x + self.w > 1.0:
            raise ValueError("x + w must be <= 1.0")
        if self.y + self.h > 1.0:
            raise ValueError("y + h must be <= 1.0")
        return self


RevisionTarget = Annotated[
    RevisionTargetPoint | RevisionTargetBox,
    Field(discriminator="kind"),
]


class RevisionEdit(BaseModel):
    """Single edit instruction for a specific target"""

    target: RevisionTarget
    instruction: str = Field(..., min_length=1, max_length=300)
    edit_type: Literal["auto", "text", "illustration", "layout", "style"] = "auto"
    expected_text: str | None = Field(default=None, max_length=120)

    @field_validator("instruction")
    @classmethod
    def normalize_instruction(cls, value: str) -> str:
        """Trim instruction and disallow blank values."""
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("instruction must not be blank")
        return trimmed

    @field_validator("expected_text")
    @classmethod
    def normalize_expected_text(cls, value: str | None) -> str | None:
        """Normalize optional expected text."""
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed if trimmed else None


class CreateRevisionRequest(BaseModel):
    """Request payload for creating a revision generation"""

    global_instruction: str | None = Field(default=None, max_length=500)
    edits: list[RevisionEdit] = Field(..., min_length=1, max_length=5)

    @field_validator("global_instruction")
    @classmethod
    def normalize_global_instruction(cls, value: str | None) -> str | None:
        """Normalize global instruction text."""
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed if trimmed else None


class RevisionCreateResponse(BaseModel):
    """Response payload after creating a revision request"""

    generation_id: str
    generation_type: GenerationTypeEnum = GenerationTypeEnum.REVISION
