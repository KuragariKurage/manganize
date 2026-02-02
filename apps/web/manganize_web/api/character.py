"""API endpoints for character management"""

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from manganize_web.models.database import get_db_session
from manganize_web.repositories.database_session import DatabaseSession
from manganize_web.schemas.character import (
    CharacterCreate,
    CharacterListResponse,
    CharacterResponse,
    CharacterUpdate,
    SpeechStyle,
)
from manganize_web.services.character import character_service
from manganize_web.utils import image_processing

router = APIRouter()


@router.get("/characters", response_model=list[CharacterListResponse])
async def list_characters(
    db_session: DatabaseSession = Depends(get_db_session),
) -> list[CharacterListResponse]:
    """
    Get all characters (simplified list).

    Returns:
        List of characters with basic information
    """
    characters = await character_service.list_characters(db_session)
    return [CharacterListResponse.model_validate(char) for char in characters]


@router.get("/characters/{name}", response_model=CharacterResponse)
async def get_character(
    name: str,
    db_session: DatabaseSession = Depends(get_db_session),
) -> CharacterResponse:
    """
    Get character by name.

    Args:
        name: Character name

    Returns:
        Character details

    Raises:
        HTTPException: If character not found
    """
    character = await character_service.get_character(name, db_session)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    return CharacterResponse.model_validate(character)


@router.post("/characters", response_model=CharacterResponse, status_code=201)
async def create_character(
    name: str = Form(...),
    display_name: str = Form(...),
    nickname: str | None = Form(None),
    attributes: str = Form(...),
    personality: str = Form(...),
    speech_style: str = Form(...),
    portrait_image: UploadFile | None = File(None),
    full_body_image: UploadFile | None = File(None),
    db_session: DatabaseSession = Depends(get_db_session),
) -> CharacterResponse:
    """
    Create a new character with optional reference images.

    Args:
        name: Character name (ASCII only)
        display_name: Display name
        nickname: Nickname (optional)
        attributes: Comma-separated attributes
        personality: Personality description
        speech_style: Speech style (JSON string)
        portrait_image: Portrait image (optional)
        full_body_image: Full body image (optional)

    Returns:
        Created character

    Raises:
        HTTPException: If character with same name already exists or validation fails
    """
    # Parse attributes (comma-separated)
    attributes_list = [attr.strip() for attr in attributes.split(",") if attr.strip()]

    # Parse speech_style (JSON string)
    try:
        speech_style_dict = json.loads(speech_style)
        speech_style_obj = SpeechStyle(**speech_style_dict)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid speech_style format: {str(e)}",
        )

    # Create character data
    character_data = CharacterCreate(
        name=name,
        display_name=display_name,
        nickname=nickname if nickname else None,
        attributes=attributes_list,
        personality=personality,
        speech_style=speech_style_obj,
    )

    # Create character
    character = await character_service.create_character(character_data, db_session)

    # Save images if provided
    if portrait_image and portrait_image.filename:
        await character_service.save_character_image(
            name, "portrait", portrait_image, db_session
        )

    if full_body_image and full_body_image.filename:
        await character_service.save_character_image(
            name, "full_body", full_body_image, db_session
        )

    # Refresh character to get updated reference_images
    character = await character_service.get_character(name, db_session)
    return CharacterResponse.model_validate(character)


@router.put("/characters/{name}", response_model=CharacterResponse)
async def update_character(
    name: str,
    display_name: str | None = Form(None),
    nickname: str | None = Form(None),
    attributes: str | None = Form(None),
    personality: str | None = Form(None),
    speech_style: str | None = Form(None),
    portrait_image: UploadFile | None = File(None),
    full_body_image: UploadFile | None = File(None),
    db_session: DatabaseSession = Depends(get_db_session),
) -> CharacterResponse:
    """
    Update an existing character with optional reference images.

    Args:
        name: Character name
        display_name: Display name (optional)
        nickname: Nickname (optional)
        attributes: Comma-separated attributes (optional)
        personality: Personality description (optional)
        speech_style: Speech style (JSON string, optional)
        portrait_image: Portrait image (optional)
        full_body_image: Full body image (optional)

    Returns:
        Updated character

    Raises:
        HTTPException: If character not found or validation fails
    """
    # Parse attributes if provided
    attributes_list = None
    if attributes is not None:
        attributes_list = [
            attr.strip() for attr in attributes.split(",") if attr.strip()
        ]

    # Parse speech_style if provided
    speech_style_obj = None
    if speech_style is not None:
        try:
            speech_style_dict = json.loads(speech_style)
            speech_style_obj = SpeechStyle(**speech_style_dict)
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid speech_style format: {str(e)}",
            )

    # Create update data
    character_data = CharacterUpdate(
        display_name=display_name,
        nickname=nickname,
        attributes=attributes_list,
        personality=personality,
        speech_style=speech_style_obj,
    )

    # Update character
    character = await character_service.update_character(
        name, character_data, db_session
    )

    # Save images if provided
    if portrait_image and portrait_image.filename:
        await character_service.save_character_image(
            name, "portrait", portrait_image, db_session
        )

    if full_body_image and full_body_image.filename:
        await character_service.save_character_image(
            name, "full_body", full_body_image, db_session
        )

    # Refresh character to get updated reference_images
    character = await character_service.get_character(name, db_session)
    return CharacterResponse.model_validate(character)


@router.delete("/characters/{name}", status_code=204)
async def delete_character(
    name: str,
    db_session: DatabaseSession = Depends(get_db_session),
) -> None:
    """
    Delete a character.

    Args:
        name: Character name

    Raises:
        HTTPException: If character not found or is default character
    """
    await character_service.delete_character(name, db_session)


@router.get("/characters/{name}/image")
async def get_character_image(
    name: str,
    image_type: str = "portrait",
    db_session: DatabaseSession = Depends(get_db_session),
) -> Response:
    """
    Get character reference image.

    Args:
        name: Character name
        image_type: Image type ('portrait' or 'full_body')

    Returns:
        Image file

    Raises:
        HTTPException: If character or image not found
    """
    character = await character_service.get_character(name, db_session)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if not character.reference_images or image_type not in character.reference_images:
        raise HTTPException(status_code=404, detail="Image not found")

    # Load image from disk
    image_data = await image_processing.load_character_image(name, image_type)

    # Determine media type based on file extension
    image_path = image_processing.get_character_image_path(name, image_type)
    if image_path:
        ext = image_path.suffix.lower()
        media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
    else:
        media_type = "image/png"

    return Response(
        content=image_data,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=31536000",
        },
    )
