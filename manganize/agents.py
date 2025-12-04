from datetime import datetime
from typing import Optional, TypedDict

from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.messages import SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from manganize.prompts import (
    MANGANIZE_RESEARCHER_SYSTEM_PROMPT,
    MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT,
)
from manganize.tools import generate_manga_image, retrieve_webpage


class ManganizeInput(TypedDict):
    topic: str


class ManganizeState(TypedDict):
    research_results: str
    scenario: str


class ManganizeOutput(TypedDict):
    generated_image: Optional[bytes]


class ManganizeAgentState(
    ManganizeInput,
    ManganizeState,
    ManganizeOutput,
):
    pass


class ManganizeAgent:
    def __init__(self, model: BaseChatModel | None = None):
        today_date = datetime.now().strftime("%Y-%m-%d")

        today_prompt = f"""
        # 今日の日付
        今日は{today_date}です。
        """

        self.researcher = create_agent(
            model=model or init_chat_model(model="google_genai:gemini-3-pro-preview"),
            tools=[retrieve_webpage, DuckDuckGoSearchRun()],
            system_prompt=SystemMessage(
                content=MANGANIZE_RESEARCHER_SYSTEM_PROMPT + today_prompt
            ),
        )
        self.scenario_writer = create_agent(
            model=model or init_chat_model(model="google_genai:gemini-3-pro-preview"),
            system_prompt=SystemMessage(
                content=MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT + today_prompt
            ),
        )

    def _researcher_node(self, state: ManganizeAgentState) -> Command:
        result = self.researcher.invoke(
            {"messages": [{"role": "user", "content": state["topic"]}]}
        )
        last_message = result["messages"][-1]
        content = (
            last_message.content
            if isinstance(last_message.content, str)
            else str(last_message.content)
        )
        return Command(
            update={
                "research_results": content,
            },
            goto="scenario_writer",
        )

    def _scenario_writer_node(self, state: ManganizeAgentState) -> Command:
        result = self.scenario_writer.invoke(
            {"messages": [{"role": "user", "content": state["research_results"]}]}
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

    def compile_graph(self) -> StateGraph:
        builder = StateGraph(
            state_schema=ManganizeAgentState,
            input_schema=ManganizeInput,
            output_schema=ManganizeOutput,
        )

        builder.add_node("researcher", self._researcher_node)
        builder.add_node("scenario_writer", self._scenario_writer_node)
        builder.add_node("image_generator", self._image_generator_node)

        builder.add_edge(START, "researcher")
        builder.add_edge("researcher", "scenario_writer")
        builder.add_edge("scenario_writer", "image_generator")

        return builder.compile(checkpointer=InMemorySaver())
