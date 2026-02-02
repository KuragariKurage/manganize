"""Character management service"""

from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm.attributes import flag_modified

from manganize_web.models.character import Character
from manganize_web.repositories.database_session import DatabaseSession
from manganize_web.schemas.character import CharacterCreate, CharacterUpdate
from manganize_web.utils import image_processing


class CharacterService:
    """Service for managing manga characters"""

    async def list_characters(self, db_session: DatabaseSession) -> list[Character]:
        """
        Get all characters.

        Args:
            db_session: Database session

        Returns:
            List of all characters
        """
        return await db_session.characters.list_all()

    async def get_character(
        self, name: str, db_session: DatabaseSession
    ) -> Character | None:
        """
        Get character by name.

        Args:
            name: Character name
            db_session: Database session

        Returns:
            Character if found, None otherwise
        """
        return await db_session.characters.get_by_name(name)

    async def create_character(
        self,
        character_data: CharacterCreate,
        db_session: DatabaseSession,
    ) -> Character:
        """
        Create a new character.

        Args:
            character_data: Character creation data
            db_session: Database session

        Returns:
            Created character

        Raises:
            HTTPException: If character with same name already exists
        """
        # Check if character already exists
        existing = await db_session.characters.get_by_name(character_data.name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Character with name '{character_data.name}' already exists",
            )

        # Create character model
        character = Character(
            name=character_data.name,
            display_name=character_data.display_name,
            nickname=character_data.nickname,
            attributes=character_data.attributes,
            personality=character_data.personality,
            speech_style=character_data.speech_style.model_dump(),
            reference_images=None,  # Images handled separately
            is_default=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        await db_session.characters.create(character)
        await db_session.commit()

        return character

    async def update_character(
        self,
        name: str,
        character_data: CharacterUpdate,
        db_session: DatabaseSession,
    ) -> Character:
        """
        Update an existing character.

        Args:
            name: Character name
            character_data: Character update data
            db_session: Database session

        Returns:
            Updated character

        Raises:
            HTTPException: If character not found or is default character
        """
        character = await db_session.characters.get_by_name(name)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        if character.is_default:
            raise HTTPException(
                status_code=403,
                detail="Cannot modify default character",
            )

        # Update only provided fields
        if character_data.display_name is not None:
            character.display_name = character_data.display_name
        if character_data.nickname is not None:
            character.nickname = character_data.nickname
        if character_data.attributes is not None:
            character.attributes = character_data.attributes
        if character_data.personality is not None:
            character.personality = character_data.personality
        if character_data.speech_style is not None:
            character.speech_style = character_data.speech_style.model_dump()

        character.updated_at = datetime.now(timezone.utc)

        await db_session.commit()
        return character

    async def save_character_image(
        self,
        name: str,
        image_type: str,
        image_file: UploadFile,
        db_session: DatabaseSession,
    ) -> Character:
        """
        Save character reference image and update database.

        Args:
            name: Character name
            image_type: Image type ('portrait' or 'full_body')
            image_file: Uploaded image file
            db_session: Database session

        Returns:
            Updated character

        Raises:
            HTTPException: If character not found or image save fails
        """
        character = await db_session.characters.get_by_name(name)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        # Save image to disk and get relative path
        relative_path = await image_processing.save_character_image(
            name, image_type, image_file
        )

        # Update reference_images in database
        if character.reference_images is None:
            character.reference_images = {}

        character.reference_images[image_type] = relative_path
        character.updated_at = datetime.now(timezone.utc)

        # Mark reference_images as modified for SQLAlchemy to detect changes
        flag_modified(character, "reference_images")

        await db_session.commit()
        return character

    async def delete_character(self, name: str, db_session: DatabaseSession) -> None:
        """
        Delete a character and its reference images.

        Args:
            name: Character name
            db_session: Database session

        Raises:
            HTTPException: If character not found or is default character
        """
        character = await db_session.characters.get_by_name(name)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        if character.is_default:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete default character",
            )

        # Delete from database first
        await db_session.characters.delete(character)
        await db_session.commit()

        # Then delete image files
        image_processing.delete_character_images(name)


# Global instance
character_service = CharacterService()
