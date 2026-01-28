from datetime import datetime
from enum import StrEnum
from typing import Literal, Optional, TypedDict

from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.messages import SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

from manganize_core.character import BaseCharacter, KurageChan
from manganize_core.prompts import (
    get_researcher_system_prompt,
    get_scenario_writer_system_prompt,
)
from manganize_core.tools import generate_manga_image, read_document_file, retrieve_webpage


class NodeName(StrEnum):
    """Graph node names as constants"""

    RESEARCHER = "researcher"
    SCENARIO_WRITER = "scenario_writer"
    IMAGE_GENERATOR = "image_generator"


# Number of processing nodes (excluding START/END)
PROCESSING_NODE_COUNT = 3


class ManganizeInput(TypedDict):
    topic: str


class ManganizeState(TypedDict):
    research_results: str
    research_results_relevance: float
    scenario: str


class ManganizeOutput(TypedDict):
    topic_title: str
    generated_image: Optional[bytes]


class ManganizeAgentState(
    ManganizeInput,
    ManganizeState,
    ManganizeOutput,
):
    pass


class ResearcherAgentOutput(BaseModel):
    topic_title: str = Field(description="トピックのタイトル")
    output: str = Field(description="構造化されたネタ帳（ファクトシート）の出力内容")
    relevance: float = Field(
        description="ユーザの入力に対する出力内容の関連度（0.0から1.0の間）。1.0に近いほど関連度が高い。"
    )


class ManganizeAgent:
    def __init__(
        self,
        character: BaseCharacter | None = None,
        researcher_llm: BaseChatModel | None = None,
        scenario_writer_llm: BaseChatModel | None = None,
        relevance_threshold: float = 0.5,
    ):
        # キャラクターの設定（デフォルトはくらげちゃん）
        self.character = character or KurageChan()

        today_date = datetime.now().strftime("%Y-%m-%d")

        self.today_prompt = f"""
        # 今日の日付
        今日は{today_date}です。
        """

        self.researcher = create_agent(
            model=researcher_llm
            or init_chat_model(model="google_genai:gemini-2.5-pro"),
            tools=[retrieve_webpage, DuckDuckGoSearchRun(), read_document_file],
            system_prompt=SystemMessage(content=get_researcher_system_prompt()),
            response_format=ResearcherAgentOutput,
        )
        self.scenario_writer = create_agent(
            model=scenario_writer_llm
            or init_chat_model(model="google_genai:gemini-2.5-flash"),
            system_prompt=SystemMessage(
                content=get_scenario_writer_system_prompt(self.character)
            ),
        )

        self.relevance_threshold = relevance_threshold

    def _researcher_node(self, state: ManganizeAgentState) -> Command:
        result = self.researcher.invoke(
            {
                "messages": [
                    {"role": "user", "content": state["topic"] + self.today_prompt}
                ]
            }
        )
        response = result["structured_response"]

        topic_title = response.topic_title
        content = response.output
        relevance = response.relevance

        return Command(
            update={
                "topic_title": topic_title,
                "research_results": content,
                "research_results_relevance": relevance,
            },
        )

    def _scenario_writer_node(self, state: ManganizeAgentState) -> Command:
        result = self.scenario_writer.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": state["research_results"] + self.today_prompt,
                    }
                ]
            }
        )

        last_message = result["messages"][-1]
        content = (
            last_message.content
            if isinstance(last_message.content, str)
            else str(last_message.content)
        )
        return Command(
            update={
                "scenario": content,
            },
            goto=NodeName.IMAGE_GENERATOR,
        )

    def _image_generator_node(self, state: ManganizeAgentState) -> Command:
        result = generate_manga_image(state["scenario"], self.character)
        return Command(update={"generated_image": result}, goto=END)

    def _check_relevance(
        self, state: ManganizeAgentState
    ) -> Literal["researcher_is_not_relevant", "researcher_is_relevant"]:
        if state["research_results_relevance"] < self.relevance_threshold:
            return "researcher_is_not_relevant"
        else:
            return "researcher_is_relevant"

    def compile_graph(
        self, checkpointer: BaseCheckpointSaver | None = None
    ) -> CompiledStateGraph:
        if checkpointer is None:
            checkpointer = InMemorySaver()

        builder = StateGraph(
            state_schema=ManganizeAgentState,  # type: ignore
            input_schema=ManganizeInput,  # type: ignore
            output_schema=ManganizeOutput,  # type: ignore
        )

        builder.add_node(NodeName.RESEARCHER, self._researcher_node)
        builder.add_node(NodeName.SCENARIO_WRITER, self._scenario_writer_node)
        builder.add_node(NodeName.IMAGE_GENERATOR, self._image_generator_node)

        builder.add_edge(START, NodeName.RESEARCHER)
        builder.add_conditional_edges(
            NodeName.RESEARCHER,
            self._check_relevance,
            path_map={
                "researcher_is_not_relevant": END,
                "researcher_is_relevant": NodeName.SCENARIO_WRITER,
            },
        )
        builder.add_edge(NodeName.SCENARIO_WRITER, NodeName.IMAGE_GENERATOR)

        return builder.compile(checkpointer=checkpointer)
