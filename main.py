import argparse
from datetime import datetime
from io import BytesIO
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from PIL import Image

from manganize.agents import ManganizeAgent


def local_graph():
    return ManganizeAgent(
        model=init_chat_model(model="google_genai:gemini-2.5-flash")
    ).compile_graph()


def main():
    parser = argparse.ArgumentParser(
        description="テキストやURLをマンガ画像に変換します"
    )
    parser.add_argument("source", help="変換するURLまたはテキスト")

    args = parser.parse_args()

    graph = local_graph()

    config: RunnableConfig = {"configurable": {"thread_id": "1"}}

    for chunk in graph.stream({"topic": args.source}, config, stream_mode="values"):
        if chunk.get("generated_image"):
            output_dir = (
                Path(__file__).parent
                / "output"
                / datetime.now().strftime("%Y%m%d_%H%M%S")
            )
            output_dir.mkdir(parents=True, exist_ok=True)

            image = Image.open(BytesIO(chunk.get("generated_image")))
            image_filename = (
                f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            image.save(output_dir / image_filename)

            research_results_filename = (
                f"research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            Path(output_dir / research_results_filename).write_text(
                chunk.get("research_results")
            )
            scenario_filename = (
                f"scenario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            Path(output_dir / scenario_filename).write_text(chunk.get("scenario"))
            print("artifacts saved.")
            break


if __name__ == "__main__":
    main()
