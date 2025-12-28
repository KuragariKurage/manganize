"""Pydantic schemas for manga generation requests and responses"""

from datetime import datetime

from pydantic import BaseModel, Field

from web.models.generation import GenerationStatusEnum


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
