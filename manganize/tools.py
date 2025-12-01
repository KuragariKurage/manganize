from pathlib import Path

import requests
from google import genai
from google.genai import types
from langchain.tools import tool

from manganize.prompts import MANGANIZE_IMAGE_GENERATION_SYSTEM_PROMPT


def load_kurage_image() -> bytes:
    image_path = Path(__file__).parent.parent / "assets" / "kurage.png"
    return image_path.read_bytes()


def load_kurage_full_image() -> bytes:
    image_path = Path(__file__).parent.parent / "assets" / "kurage2.png"
    return image_path.read_bytes()


def generate_manga_image(content: str) -> bytes | None:
    """マンガの作画を行うエージェントです。

    指定されたコンテンツに基づいて、Gemini 3 Pro Image Previewモデルを使用して
    漫画風の画像を生成します。生成された画像はPNG形式のバイト列として
    状態に保存されます。

    Args:
        content (str): 画像生成のためのコンテンツ。
                      漫画化したいテキストやストーリーの説明を含む。

    Returns:
        Command: LangGraphのCommandオブジェクト。
                - 成功時: update={"generated_image": bytes} で画像データ（PNG形式）を含む
                - 失敗時: update={"generated_image": None, "message": [ToolMessage]} でエラーメッセージを含む

    Note:
        - 画像は9:16のアスペクト比、2Kサイズで生成されます
        - Google Searchツールが有効化されており、必要に応じて検索が実行されます
        - 生成された画像にはコミックスのロゴなどの明示的なスタイル表記は含まれません

    Example:
        >>> command = generate_manga_image("可愛い女の子が笑顔で挨拶している")
        >>> if command.update.get("generated_image"):
        >>>     image = Image.open(io.BytesIO(command.update["generated_image"]))
        >>>     image.save("manga.png")
    """

    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[
            types.Part.from_bytes(
                data=load_kurage_image(),
                mime_type="image/png",
            ),
            types.Part.from_bytes(
                data=load_kurage_full_image(),
                mime_type="image/png",
            ),
            types.Part.from_text(text=f"脚本:\n{content}"),
        ],
        config=types.GenerateContentConfig(
            system_instruction=MANGANIZE_IMAGE_GENERATION_SYSTEM_PROMPT,
            image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K"),
            tools=[{"google_search": {}}],
        ),
    )

    image_parts = [part for part in response.parts if part.inline_data]

    if image_parts:
        # inline_dataから直接バイトデータを取得
        image_data = image_parts[0].inline_data.data
        if image_data:
            return image_data

    return None


@tool
def retrieve_webpage(url: str) -> str:
    """指定されたURLのウェブページを取得するツール。"""

    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return response.text
