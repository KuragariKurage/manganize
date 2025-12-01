from typing import Any

from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.messages import SystemMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver

from manganize.prompts import (
    MANGANIZE_RESEARCHER_SYSTEM_PROMPT,
    MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT,
)
from manganize.tools import generate_manga_image, retrieve_webpage


class ManganizeAgent:
    def __init__(self, model: BaseChatModel | None = None):
        self.researcher = create_agent(
            model=model or init_chat_model(model="google_genai:gemini-3-pro-preview"),
            tools=[retrieve_webpage, DuckDuckGoSearchRun()],
            system_prompt=SystemMessage(content=MANGANIZE_RESEARCHER_SYSTEM_PROMPT),
            checkpointer=InMemorySaver(),
        )
        self.scenario_writer = create_agent(
            model=model or init_chat_model(model="google_genai:gemini-3-pro-preview"),
            system_prompt=SystemMessage(
                content=MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT
            ),
            checkpointer=InMemorySaver(),
        )

    def __call__(self, input_text: str, thread_id: str) -> dict[str, Any]:
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        messages = {"messages": input_text}

        researcher_response = self.researcher.invoke(messages, config)

        # researcher の応答内容を取得し、文字列として scenario_writer に渡す
        last_message = researcher_response.get("messages")[-1]
        # AIMessage の content を取得（辞書形式の可能性があるため処理）
        if isinstance(last_message.content, dict):
            content = last_message.content.get("text", str(last_message.content))
        else:
            content = str(last_message.content)

        # 新しいユーザー入力として渡す
        messages_to_scenario_writer = {"messages": content}

        scenario_writer_response = self.scenario_writer.invoke(
            messages_to_scenario_writer, config
        )

        # scenario_writer の応答内容を取得
        scenario_message = scenario_writer_response.get("messages")[-1]
        if isinstance(scenario_message.content, dict):
            scenario_content = scenario_message.content.get(
                "text", str(scenario_message.content)
            )
        else:
            scenario_content = str(scenario_message.content)

        return {
            "generated_image": generate_manga_image(scenario_content),
        }
