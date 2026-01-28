from datetime import datetime, timezone
from enum import Enum
from typing import AsyncGenerator, Optional

from bedrock_agentcore import BedrockAgentCoreApp
from langgraph_checkpoint_aws import AgentCoreMemorySaver
from pydantic import BaseModel

from manganize_core.agents import ManganizeAgent, NodeName
from manganize_core.character import BaseCharacter

app = BedrockAgentCoreApp()


checkpoint_saver = AgentCoreMemorySaver(memory_id="manganize-agent")


class GenerationStatusEnum(str, Enum):
    """Valid status values for manga generation"""

    PENDING = "pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"


class GenerationStatus(BaseModel):
    """Schema for generation status updates via SSE"""

    status: GenerationStatusEnum
    message: str
    title: Optional[str] = None
    image_data: Optional[bytes] = None

    model_config = {"use_enum_values": True}


@app.entrypoint
async def stream_manganize(payload: dict) -> AsyncGenerator[dict, None]:
    character: None | dict = payload.get("character")
    if not character:
        raise ValueError("character is required")

    character = BaseCharacter(**character)
    if not character:
        raise ValueError("Character is invalid")

    agent = ManganizeAgent(character)
    graph = agent.compile_graph(checkpointer=checkpoint_saver)

    topic: None | str = payload.get("topic")
    if not topic:
        raise ValueError("topic is required")

    # Update status: Researching
    yield GenerationStatus(
        status=GenerationStatusEnum.RESEARCHING,
        message="トピックをリサーチ中...",
    )

    image_data: bytes | None = None
    title: str = ""
    async for chunk in graph.astream(
        {"topic": topic},
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
                status=GenerationStatusEnum.WRITING,
                message="シナリオを作成中...",
            )

        # Process scenario writer node results
        if chunk.get(NodeName.SCENARIO_WRITER):
            # Update status: Generating image
            yield GenerationStatus(
                status=GenerationStatusEnum.GENERATING,
                message="画像を生成中...",
            )

        # Process image generator node results
        if results := chunk.get(NodeName.IMAGE_GENERATOR):
            # Image generation is done
            image_data = results.get("generated_image")

    # Update status: Saving
    if image_data is None:
        yield GenerationStatus(
            status=GenerationStatusEnum.ERROR,
            message="画像生成に失敗しました",
        )
        return

    yield GenerationStatus(
        status=GenerationStatusEnum.COMPLETED,
        message="生成完了！",
        title=title,
        image_data=image_data,
    )
