from datetime import datetime
from typing import Literal, Optional, TypedDict

from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.messages import SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

from manganize.prompts import (
    MANGANIZE_RESEARCHER_SYSTEM_PROMPT,
    MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT,
)
from manganize.tools import generate_manga_image, read_document_file, retrieve_webpage


class ManganizeInput(TypedDict):
    topic: str


class ManganizeState(TypedDict):
    research_results: str
    research_results_relevance: float
    scenario: str


class ManganizeOutput(TypedDict):
    generated_image: Optional[bytes]


class ManganizeAgentState(
    ManganizeInput,
    ManganizeState,
    ManganizeOutput,
):
    pass


class ResearcherAgentOutput(BaseModel):
    output: str = Field(description="構造化されたネタ帳（ファクトシート）の出力内容")
    relevance: float = Field(
        description="ユーザの入力に対する出力内容の関連度（0.0から1.0の間）。1.0に近いほど関連度が高い。"
    )


class ManganizeAgent:
    def __init__(
        self,
        researcher_llm: BaseChatModel | None = None,
        scenario_writer_llm: BaseChatModel | None = None,
        relevance_threshold: float = 0.5,
    ):
        today_date = datetime.now().strftime("%Y-%m-%d")

        self.today_prompt = f"""
        # 今日の日付
        今日は{today_date}です。
        """

        self.researcher = create_agent(
            model=researcher_llm
            or init_chat_model(model="google_genai:gemini-3-pro-preview"),
            tools=[retrieve_webpage, DuckDuckGoSearchRun(), read_document_file],
            system_prompt=SystemMessage(content=MANGANIZE_RESEARCHER_SYSTEM_PROMPT),
            response_format=ResearcherAgentOutput,
        )
        self.scenario_writer = create_agent(
            model=scenario_writer_llm
            or init_chat_model(model="google_genai:gemini-3-pro-preview"),
            system_prompt=SystemMessage(
                content=MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT
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

        content = response.output
        relevance = response.relevance

        return Command(
            update={
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
            goto="image_generator",
        )

    def _image_generator_node(self, state: ManganizeAgentState) -> Command:
        result = generate_manga_image(state["scenario"])
        return Command(update={"generated_image": result}, goto=END)

    def _check_relevance(
        self, state: ManganizeAgentState
    ) -> Literal["researcher_is_not_relevant", "researcher_is_relevant"]:
        if state["research_results_relevance"] < self.relevance_threshold:
            return "researcher_is_not_relevant"
        else:
            return "researcher_is_relevant"

    def compile_graph(self) -> CompiledStateGraph:
        builder = StateGraph(
            state_schema=ManganizeAgentState,  # type: ignore
            input_schema=ManganizeInput,  # type: ignore
            output_schema=ManganizeOutput,  # type: ignore
        )

        builder.add_node("researcher", self._researcher_node)
        builder.add_node("scenario_writer", self._scenario_writer_node)
        builder.add_node("image_generator", self._image_generator_node)

        builder.add_edge(START, "researcher")
        builder.add_conditional_edges(
            "researcher",
            self._check_relevance,
            path_map={
                "researcher_is_not_relevant": END,
                "researcher_is_relevant": "scenario_writer",
            },
        )
        builder.add_edge("scenario_writer", "image_generator")

        return builder.compile(checkpointer=InMemorySaver())
