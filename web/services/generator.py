"""Manga generation service that wraps ManganizeAgent with SSE progress callbacks"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from web.models.generation import GenerationHistory, GenerationStatusEnum
from web.repositories.database_session import DatabaseSession
from web.schemas.generation import GenerationStatus

# Heavy dependencies are lazily imported in methods to speed up server startup
if TYPE_CHECKING:
    from manganize.character import BaseCharacter


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

    async def create_generation_request(
        self,
        topic: str,
        character_name: str,
        db_session: DatabaseSession,
    ) -> str:
        """
        Create a new generation request.

        Args:
            topic: Topic to generate manga about
            character_name: Character to use
            db_session: Database session with repositories

        Returns:
            generation_id: UUID of the created generation
        """
        generation_id = str(uuid.uuid4())

        generation = GenerationHistory(
            id=generation_id,
            character_name=character_name,
            input_topic=topic,
            generated_title="",  # Will be filled after generation
            status=GenerationStatusEnum.PENDING,
            created_at=datetime.now(timezone.utc),
        )

        await db_session.generations.create(generation)
        await db_session.commit()

        return generation_id

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
        from manganize.character import KurageChan

        character = await db_session.characters.get_by_name(character_name)

        if not character:
            # Fallback to default character
            return KurageChan()

        # For now, just return KurageChan
        # TODO: Create dynamic character from database in Phase 5
        return KurageChan()

    async def generate_manga(
        self,
        generation_id: str,
        topic: str,
        character_name: str,
        db_session: DatabaseSession,
    ) -> AsyncGenerator[GenerationStatus, None]:
        """
        Generate manga image with SSE progress updates.

        Args:
            generation_id: UUID for this generation
            topic: Topic to generate manga about
            character_name: Character to use
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
            from manganize.agents import ManganizeAgent, NodeName

            # Create ManganizeAgent
            agent = ManganizeAgent(character=character)
            graph = agent.compile_graph()

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
                {"topic": topic},
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


# Global instance
generator_service = GeneratorService()
