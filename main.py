import argparse
from datetime import datetime
from io import BytesIO
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from PIL import Image

from manganize.agents import ManganizeAgent
from manganize.character import BaseCharacter, KurageChan


def local_graph(
    character: BaseCharacter | None = None, relevance_threshold: float = 0.5
) -> CompiledStateGraph:
    return ManganizeAgent(
        character=character or KurageChan(),
        researcher_llm=init_chat_model(model="google_genai:gemini-2.5-pro"),
        scenario_writer_llm=init_chat_model(model="google_genai:gemini-2.5-flash"),
        relevance_threshold=relevance_threshold,
    ).compile_graph()


def main():
    parser = argparse.ArgumentParser(
        description="テキストやURLをマンガ画像に変換します"
    )
    parser.add_argument("source", help="変換するURLまたはテキスト")
    parser.add_argument(
        "--character",
        "-c",
        type=str,
        help="キャラクター設定ファイル（YAML）のパス。指定しない場合はデフォルト（くらげちゃん）を使用",
    )

    args = parser.parse_args()

    # キャラクターの読み込み
    character: BaseCharacter | None = None
    if args.character:
        character_path = Path(args.character)
        if not character_path.exists():
            print(f"エラー: キャラクターファイルが見つかりません: {args.character}")
            return
        try:
            character = BaseCharacter.from_yaml(character_path)
            print(f"キャラクター '{character.name}' を読み込みました")
        except Exception as e:
            print(f"エラー: キャラクターファイルの読み込みに失敗しました: {e}")
            return

    relevance_threshold = 0.5
    graph = local_graph(character, relevance_threshold)

    config: RunnableConfig = {"configurable": {"thread_id": "1"}}

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "output" / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    for chunk in graph.stream({"topic": args.source}, config, stream_mode="values"):
        if research_results := chunk.get("research_results"):
            research_results_filename = f"research_results_{date_str}.txt"
            research_results_path = Path(output_dir / research_results_filename)
            if not research_results_path.exists():
                print("research results generated.")
                research_results_path.write_text(research_results)

        if scenario := chunk.get("scenario"):
            scenario_filename = f"scenario_{date_str}.txt"
            scenario_path = Path(output_dir / scenario_filename)
            if not scenario_path.exists():
                print("scenario generated.")
                scenario_path.write_text(scenario)

        if research_results_relevance := chunk.get("research_results_relevance"):
            if research_results_relevance < relevance_threshold:
                print("research results is not relevant. stop processing.")
                break

        if generated_image := chunk.get("generated_image"):
            image = Image.open(BytesIO(generated_image))
            image_filename = f"generated_image_{date_str}.png"
            image.save(output_dir / image_filename)
            print("image generated.")
            break


if __name__ == "__main__":
    main()
