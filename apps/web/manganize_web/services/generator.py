"""Manga generation service that wraps ManganizeAgent with SSE progress callbacks"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from manganize_web.models.generation import (
    GenerationHistory,
    GenerationStatusEnum,
    GenerationTypeEnum,
)
from manganize_web.repositories.database_session import DatabaseSession
from manganize_web.schemas.generation import GenerationStatus
from manganize_web.services.upload_source import upload_source_service

# Heavy dependencies are lazily imported in methods to speed up server startup
if TYPE_CHECKING:
    from manganize_core.character import BaseCharacter


# Progress milestones for each stage
class ProgressMilestone:
    """Progress percentage constants for each generation stage"""

    STARTED = 10
    RESEARCHING = 20
    WRITING = 50
    GENERATING = 75
    SAVING = 90
    COMPLETED = 100


class GeneratorService:
    """Service for generating manga images with progress tracking"""

    def __init__(self) -> None:
        """Initialize generator service"""
        pass

    def _compose_agent_topic(self, topic: str, source_url: str | None) -> str:
        """
        Compose final topic text sent to the researcher agent.

        If a source URL exists, include an explicit tool-usage instruction
        so the agent reads the uploaded document by itself.
        """
        user_topic = topic.strip()
        if not source_url:
            return user_topic

        source_instruction = (
            "添付ドキュメントがあります。以下のURLを `read_document_file` ツールで"
            "必ず読み込んでから、内容に基づいて構成してください。\n"
            f"{source_url}"
        )
        if user_topic:
            return f"{user_topic}\n\n{source_instruction}"
        return source_instruction

    async def create_generation_request(
        self,
        topic: str,
        character_name: str,
        upload_id: str | None,
        db_session: DatabaseSession,
    ) -> str:
        """
        Create a new initial generation request.

        Args:
            topic: Topic to generate manga about
            character_name: Character to use
            upload_id: Optional uploaded source ID
            db_session: Database session with repositories

        Returns:
            generation_id: UUID of the created generation
        """
        normalized_topic = topic.strip()
        if not normalized_topic and not upload_id:
            raise ValueError("Topic or upload_id is required")

        if upload_id:
            await upload_source_service.ensure_upload_available(upload_id, db_session)

        generation_id = str(uuid.uuid4())

        generation = GenerationHistory(
            id=generation_id,
            character_name=character_name,
            input_topic=normalized_topic,
            generated_title="",  # Will be filled after generation
            status=GenerationStatusEnum.PENDING,
            generation_type=GenerationTypeEnum.INITIAL,
            source_upload_id=upload_id,
            created_at=datetime.now(timezone.utc),
        )

        await db_session.generations.create(generation)
        await db_session.commit()

        return generation_id

    async def create_revision_request(
        self,
        parent_generation_id: str,
        revision_payload: dict[str, Any],
        db_session: DatabaseSession,
    ) -> str:
        """
        Create a new revision generation request.

        Args:
            parent_generation_id: Parent generation ID
            revision_payload: Payload that contains global instruction and edits
            db_session: Database session with repositories

        Returns:
            revision_generation_id: UUID of the created revision generation

        Raises:
            ValueError: If parent generation is not found or not editable
        """
        parent_generation = await db_session.generations.get_by_id(parent_generation_id)
        if not parent_generation:
            raise ValueError("Parent generation not found")

        if parent_generation.status != GenerationStatusEnum.COMPLETED:
            raise ValueError("Parent generation is not completed")

        if not parent_generation.image_data:
            raise ValueError("Parent generation has no image")

        revision_id = str(uuid.uuid4())
        await db_session.generations.create_revision(
            parent_generation=parent_generation,
            revision_generation_id=revision_id,
            revision_payload=revision_payload,
        )
        await db_session.commit()

        return revision_id

    async def get_generation_by_id(
        self,
        generation_id: str,
        db_session: DatabaseSession,
    ) -> GenerationHistory | None:
        """
        Get generation by ID.

        Args:
            generation_id: UUID of the generation
            db_session: Database session with repositories

        Returns:
            GenerationHistory if found, None otherwise
        """
        return await db_session.generations.get_by_id(generation_id)

    async def get_character_for_generation(
        self, character_name: str, db_session: DatabaseSession
    ) -> "BaseCharacter":
        """
        Load character configuration for generation.

        Args:
            character_name: Name of the character to use
            db_session: Database session with repositories

        Returns:
            Character instance
        """
        # Lazy import to speed up server startup
        from manganize_core.character import BaseCharacter, KurageChan, SpeechStyle

        character = await db_session.characters.get_by_name(character_name)

        if not character:
            # Fallback to default character
            return KurageChan()

        # Check if reference images are available
        if (
            not character.reference_images
            or not character.reference_images.get("portrait")
            or not character.reference_images.get("full_body")
        ):
            # If images are missing, fall back to default character
            # This can happen if character was created but images weren't uploaded
            return KurageChan()

        # Create dynamic character from database
        return BaseCharacter(
            name=character.display_name,
            nickname=character.nickname or character.display_name,
            attributes=character.attributes,
            personality=character.personality,
            speech_style=SpeechStyle(**character.speech_style),
            portrait=Path(character.reference_images["portrait"]),
            full_body=Path(character.reference_images["full_body"]),
        )

    async def generate_for_request(
        self,
        generation_id: str,
        db_session: DatabaseSession,
    ) -> AsyncGenerator[GenerationStatus, None]:
        """
        Generate image by request type (initial or revision).

        Args:
            generation_id: Generation ID
            db_session: Database session

        Yields:
            GenerationStatus updates for SSE
        """
        generation = await self.get_generation_by_id(generation_id, db_session)
        if not generation:
            raise ValueError("Generation not found")

        if generation.generation_type == GenerationTypeEnum.REVISION:
            async for status in self.generate_revision(generation_id, db_session):
                yield status
            return

        async for status in self.generate_manga(
            generation_id,
            generation.input_topic,
            generation.character_name,
            generation.source_upload_id,
            db_session,
        ):
            yield status

    async def generate_manga(
        self,
        generation_id: str,
        topic: str,
        character_name: str,
        source_upload_id: str | None,
        db_session: DatabaseSession,
    ) -> AsyncGenerator[GenerationStatus, None]:
        """
        Generate initial manga image with SSE progress updates.

        Args:
            generation_id: UUID for this generation
            topic: Topic to generate manga about
            character_name: Character to use
            source_upload_id: Optional uploaded source ID
            db_session: Database session with repositories

        Yields:
            GenerationStatus updates for SSE
        """
        try:
            # Update status: Starting
            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.RESEARCHING,
                message="リサーチを開始しています...",
                progress=ProgressMilestone.STARTED,
            )

            # Load character
            character = await self.get_character_for_generation(
                character_name, db_session
            )

            # Lazy import to speed up server startup
            from manganize_core.agents import ManganizeAgent, NodeName

            # Create ManganizeAgent
            agent = ManganizeAgent(character=character)
            graph = agent.compile_graph()

            source_url: str | None = None
            if source_upload_id:
                source_url = await upload_source_service.resolve_signed_url(
                    source_upload_id,
                    db_session,
                )
            effective_topic = self._compose_agent_topic(topic, source_url)

            # Update status: Researching
            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.RESEARCHING,
                message="トピックをリサーチ中...",
                progress=ProgressMilestone.RESEARCHING,
            )

            image_data: bytes | None = None
            title: str = ""
            async for chunk in graph.astream(
                {"topic": effective_topic},
                {"configurable": {"thread_id": generation_id}},
                stream_mode="updates",
            ):
                # Process researcher node results
                if results := chunk.get(NodeName.RESEARCHER):
                    # Get title from agent output
                    title = results.get("topic_title", "") or datetime.now(
                        timezone.utc
                    ).strftime("%Y%m%d_%H%M%S")

                    # Update status: Writing scenario
                    yield GenerationStatus(
                        id=generation_id,
                        status=GenerationStatusEnum.WRITING,
                        message="シナリオを作成中...",
                        progress=ProgressMilestone.WRITING,
                    )

                # Process scenario writer node results
                if chunk.get(NodeName.SCENARIO_WRITER):
                    # Update status: Generating image
                    yield GenerationStatus(
                        id=generation_id,
                        status=GenerationStatusEnum.GENERATING,
                        message="画像を生成中...",
                        progress=ProgressMilestone.GENERATING,
                    )

                # Process image generator node results
                if results := chunk.get(NodeName.IMAGE_GENERATOR):
                    # Image generation is done
                    image_data = results.get("generated_image")

            # Update status: Saving
            if image_data is None:
                yield GenerationStatus(
                    id=generation_id,
                    status=GenerationStatusEnum.ERROR,
                    message="画像生成に失敗しました",
                    progress=ProgressMilestone.COMPLETED,
                )
                return

            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.GENERATING,
                message="保存中...",
                progress=ProgressMilestone.SAVING,
            )

            # Save to database
            await db_session.generations.update_with_result(
                generation_id, image_data, title
            )
            await db_session.commit()

            # Update status: Completed (after DB save)
            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.COMPLETED,
                message="生成完了！",
                progress=ProgressMilestone.COMPLETED,
            )

        except Exception as e:
            # Handle errors
            error_msg = str(e)
            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.ERROR,
                message=f"エラーが発生しました: {error_msg}",
                progress=ProgressMilestone.COMPLETED,
            )

            # Save error to database
            await db_session.generations.update_error(generation_id, error_msg)
            await db_session.commit()

    async def generate_revision(
        self,
        generation_id: str,
        db_session: DatabaseSession,
    ) -> AsyncGenerator[GenerationStatus, None]:
        """
        Generate revised image from a parent image and revision payload.

        Args:
            generation_id: Revision generation ID
            db_session: Database session

        Yields:
            GenerationStatus updates for SSE
        """
        try:
            generation = await self.get_generation_by_id(generation_id, db_session)
            if not generation:
                raise ValueError("Generation not found")

            if generation.generation_type != GenerationTypeEnum.REVISION:
                raise ValueError("Generation is not a revision request")

            if not generation.parent_generation_id:
                raise ValueError("Parent generation ID is missing")

            parent_generation = await db_session.generations.get_by_id(
                generation.parent_generation_id
            )
            if not parent_generation:
                raise ValueError("Parent generation not found")

            if not parent_generation.image_data:
                raise ValueError("Parent generation has no image")

            # Load character
            character = await self.get_character_for_generation(
                generation.character_name,
                db_session,
            )

            # Lazy import to speed up server startup
            from manganize_core.tools import edit_manga_image

            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.GENERATING,
                message="修正内容を適用中...",
                progress=ProgressMilestone.STARTED,
            )

            image_data = edit_manga_image(
                content=generation.input_topic,
                base_image=parent_generation.image_data,
                revision_payload=generation.revision_payload or {},
                character=character,
            )

            if image_data is None:
                yield GenerationStatus(
                    id=generation_id,
                    status=GenerationStatusEnum.ERROR,
                    message="画像修正に失敗しました",
                    progress=ProgressMilestone.COMPLETED,
                )
                return

            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.GENERATING,
                message="保存中...",
                progress=ProgressMilestone.SAVING,
            )

            title = generation.generated_title or parent_generation.generated_title
            if title:
                if not title.endswith(" (rev)"):
                    title = f"{title} (rev)"
            else:
                title = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

            await db_session.generations.update_with_result(
                generation_id, image_data, title
            )
            await db_session.commit()

            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.COMPLETED,
                message="修正完了！",
                progress=ProgressMilestone.COMPLETED,
            )

        except Exception as e:
            error_msg = str(e)
            yield GenerationStatus(
                id=generation_id,
                status=GenerationStatusEnum.ERROR,
                message=f"エラーが発生しました: {error_msg}",
                progress=ProgressMilestone.COMPLETED,
            )

            await db_session.generations.update_error(generation_id, error_msg)
            await db_session.commit()


# Global instance
generator_service = GeneratorService()
