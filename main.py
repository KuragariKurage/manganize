import argparse
from datetime import datetime
from io import BytesIO
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from PIL import Image

from manganize.agents import ManganizeAgent


def local_graph() -> CompiledStateGraph:
    return ManganizeAgent(
        researcher_llm=init_chat_model(model="google_genai:gemini-2.5-pro"),
        scenario_writer_llm=init_chat_model(model="google_genai:gemini-2.5-flash"),
    ).compile_graph()


def main():
    parser = argparse.ArgumentParser(
        description="テキストやURLをマンガ画像に変換します"
    )
    parser.add_argument("source", help="変換するURLまたはテキスト")

    args = parser.parse_args()

    graph = local_graph()

    config: RunnableConfig = {"configurable": {"thread_id": "1"}}

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    for chunk in graph.stream({"topic": args.source}, config, stream_mode="values"):
        if research_results := chunk.get("research_results"):
            research_results_filename = f"research_results_{date_str}.txt"
            research_results_path = Path(output_dir / research_results_filename)
            if not research_results_path.exists():
                research_results_path.write_text(research_results)

        if scenario := chunk.get("scenario"):
            scenario_filename = f"scenario_{date_str}.txt"
            scenario_path = Path(output_dir / scenario_filename)
            if not scenario_path.exists():
                scenario_path.write_text(scenario)

        if generated_image := chunk.get("generated_image"):
            image = Image.open(BytesIO(generated_image))
            image_filename = f"generated_image_{date_str}.png"
            image.save(output_dir / image_filename)
            print("artifacts saved.")
            break


if __name__ == "__main__":
    main()
