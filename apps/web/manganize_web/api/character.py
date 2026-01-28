"""API endpoints for character management"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from manganize_web.models.database import get_db_session
from manganize_web.repositories.database_session import DatabaseSession
from manganize_web.schemas.character import (
    CharacterCreate,
    CharacterListResponse,
    CharacterResponse,
    CharacterUpdate,
)
from manganize_web.services.character import character_service

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
    character_data: CharacterCreate,
    db_session: DatabaseSession = Depends(get_db_session),
) -> CharacterResponse:
    """
    Create a new character.

    Args:
        character_data: Character creation data

    Returns:
        Created character

    Raises:
        HTTPException: If character with same name already exists
    """
    character = await character_service.create_character(character_data, db_session)
    return CharacterResponse.model_validate(character)


@router.put("/characters/{name}", response_model=CharacterResponse)
async def update_character(
    name: str,
    character_data: CharacterUpdate,
    db_session: DatabaseSession = Depends(get_db_session),
) -> CharacterResponse:
    """
    Update an existing character.

    Args:
        name: Character name
        character_data: Character update data

    Returns:
        Updated character

    Raises:
        HTTPException: If character not found
    """
    character = await character_service.update_character(
        name, character_data, db_session
    )
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

    # For now, return placeholder
    # TODO: Implement actual image serving in Phase 5 polish
    raise HTTPException(status_code=501, detail="Image serving not yet implemented")
