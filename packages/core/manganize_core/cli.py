"""CLI entry point for manganize — generate manga images from the terminal."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(help="Manganize: generate manga images from the terminal.")

_DEFAULT_OUTPUT_DIR = Path(".")

# Built-in characters bundled with the package
_BUILTIN_CHARACTERS = {"kurage"}


def _list_available_characters() -> list[str]:
    """Return available character names: built-ins plus any found in ./characters/."""
    names = set(_BUILTIN_CHARACTERS)
    custom_dir = Path.cwd() / "characters"
    if custom_dir.exists():
        names.update(
            d.name
            for d in custom_dir.iterdir()
            if d.is_dir() and (d / f"{d.name}.yaml").exists()
        )
    return sorted(names)


def _load_character(name: str):
    """Load a character by name.

    Built-in characters (e.g. kurage) are loaded from package assets.
    Custom characters are loaded from ./characters/<name>/<name>.yaml.
    """
    from manganize_core.character import BaseCharacter, KurageChan

    if name in _BUILTIN_CHARACTERS:
        return KurageChan()

    yaml_path = Path.cwd() / "characters" / name / f"{name}.yaml"
    if not yaml_path.exists():
        typer.echo(
            f"Character '{name}' not found (expected {yaml_path}). "
            "Falling back to kurage.",
            err=True,
        )
        return KurageChan()
    return BaseCharacter.from_yaml(yaml_path)


async def _run_generation(topic: str, character_name: str) -> bytes | None:
    """Run the ManganizeAgent pipeline and return raw image bytes."""
    from manganize_core.agents import ManganizeAgent, NodeName

    character = _load_character(character_name)
    agent = ManganizeAgent(character=character)
    graph = agent.compile_graph()

    image_data: bytes | None = None

    typer.echo("🔍 リサーチ中...")
    async for chunk in graph.astream(
        {"topic": topic},
        {"configurable": {"thread_id": f"cli-{datetime.now(timezone.utc).timestamp()}"}},
        stream_mode="updates",
    ):
        if chunk.get(NodeName.RESEARCHER):
            typer.echo("✍️  シナリオ作成中...")
        if chunk.get(NodeName.SCENARIO_WRITER):
            typer.echo("🎨 画像生成中...")
        if results := chunk.get(NodeName.IMAGE_GENERATOR):
            image_data = results.get("generated_image")

    return image_data


def _save_image(image_data: bytes, output_dir: Path, title: str = "") -> Path:
    """Save image bytes to output directory and return the saved path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_title = title.replace("/", "_").replace(" ", "_")[:40] if title else ""
    filename = f"{timestamp}_{safe_title}.png" if safe_title else f"{timestamp}.png"
    output_path = output_dir / filename
    output_path.write_bytes(image_data)
    return output_path


@app.command()
def topic(
    text: Annotated[str, typer.Argument(help="トピックまたはURL")],
    character: Annotated[
        str,
        typer.Option("--character", "-c", help="キャラクター名 (例: kurage, gpt)"),
    ] = "kurage",
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="出力ディレクトリ"),
    ] = _DEFAULT_OUTPUT_DIR,
) -> None:
    """トピックまたはURLから漫画画像を生成する。"""
    available = _list_available_characters()
    if available and character not in available:
        typer.echo(
            f"利用可能なキャラクター: {', '.join(available)}", err=True
        )
        raise typer.Exit(code=1)

    typer.echo(f"📖 トピック: {text}")
    typer.echo(f"🐙 キャラクター: {character}")

    image_data = asyncio.run(_run_generation(text, character))

    if image_data is None:
        typer.echo("❌ 画像生成に失敗しました", err=True)
        raise typer.Exit(code=1)

    saved_path = _save_image(image_data, output)
    typer.echo(f"✅ 保存しました: {saved_path}")


@app.command()
def characters() -> None:
    """利用可能なキャラクター一覧を表示する。"""
    available = _list_available_characters()
    if not available:
        typer.echo("キャラクターが見つかりません")
        return
    for name in available:
        typer.echo(f"  - {name}")


def main() -> None:
    """CLI entry point registered in pyproject.toml [project.scripts]."""
    app()


if __name__ == "__main__":
    main()
