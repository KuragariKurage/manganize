import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from google import genai
from google.genai import types
from langchain.tools import tool
from markitdown import MarkItDown
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from manganize_core.character import BaseCharacter
from manganize_core.prompts import get_image_generation_system_prompt


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=15))
def generate_manga_image(content: str, character: BaseCharacter) -> bytes | None:
    """マンガの作画を行うエージェントです。

    指定されたコンテンツとキャラクターに基づいて、Gemini 3 Pro Image Previewモデルを使用して
    漫画風の画像を生成します。生成された画像はPNG形式のバイト列として返されます。

    Args:
        content: 画像生成のためのコンテンツ。漫画化したいテキストやストーリーの説明を含む。
        character: 使用するキャラクター情報

    Returns:
        生成された画像のバイトデータ（PNG形式）、失敗時はNone

    Note:
        - 画像は9:16のアスペクト比、2Kサイズで生成されます
        - Google Searchツールが有効化されており、必要に応じて検索が実行されます
        - 生成された画像にはコミックスのロゴなどの明示的なスタイル表記は含まれません

    Example:
        >>> from manganize_core.character import KurageChan
        >>> character = KurageChan()
        >>> image_data = generate_manga_image("可愛い女の子が笑顔で挨拶している", character)
        >>> if image_data:
        >>>     image = Image.open(io.BytesIO(image_data))
        >>>     image.save("manga.png")
    """

    try:
        client = genai.Client()

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=[
                types.Part.from_bytes(
                    data=character.get_portrait_bytes(),
                    mime_type="image/png",
                ),
                types.Part.from_bytes(
                    data=character.get_full_body_bytes(),
                    mime_type="image/png",
                ),
                types.Part.from_text(text=f"脚本:\n{content}"),
            ],
            config=types.GenerateContentConfig(
                system_instruction=get_image_generation_system_prompt(character),
                image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K"),
                tools=[{"google_search": {}}],
            ),
        )

        if response.parts is None:
            return None

        image_parts = [part for part in response.parts if part.inline_data]

        if image_parts:
            # inline_dataから直接バイトデータを取得
            image_data = (
                image_parts[0].inline_data.data if image_parts[0].inline_data else None
            )
            if image_data:
                return image_data
    except Exception as e:
        raise RuntimeError(f"画像生成に失敗しました: {e}") from e

    return None


@tool
def retrieve_webpage(url: str) -> str:
    """指定されたURLのウェブページを取得し、Markdown形式で返すツール。

    Playwright を使用して JavaScript レンダリング後の HTML を取得し、
    MarkItDown で LLM 向けに最適化された Markdown に変換します。
    """

    try:
        # Playwright でページを取得
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            browser.close()

        # MarkItDown で HTML を Markdown に変換
        md = MarkItDown()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html)
            f.flush()
            temp_path = f.name

        try:
            result = md.convert(temp_path)
            return result.text_content
        finally:
            # 一時ファイルを削除
            Path(temp_path).unlink(missing_ok=True)

    except Exception as e:
        # Playwright が失敗した場合、従来の requests にフォールバック
        # ただし、Markdown 変換は行わず HTML をそのまま返す
        try:
            response = requests.get(
                url,
                timeout=10.0,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )
            response.raise_for_status()
            # フォールバック時は HTML をそのまま返す
            return response.text
        except Exception as fallback_error:
            raise RuntimeError(
                f"ウェブページの取得に失敗しました: {e}, "
                f"フォールバックも失敗: {fallback_error}"
            ) from e


@tool
def read_document_file(source: str) -> str:
    """ドキュメントファイルを読み取り、Markdown形式で返すツール。

    ローカルファイルパスまたは URL を指定できます。
    MarkItDown を使用して様々な形式のドキュメントを LLM 向けに
    最適化された Markdown に変換します。

    対応形式:
        - PDF (.pdf)
        - Word (.docx)
        - PowerPoint (.pptx)
        - Excel (.xlsx, .xls)
        - テキスト (.txt, .md, .csv, .json, .xml)
        - 画像 (.jpg, .png) - OCR とメタデータ
        - その他 MarkItDown がサポートする形式

    Args:
        source: ローカルファイルパスまたは URL

    Returns:
        Markdown 形式に変換されたドキュメント内容
    """
    md = MarkItDown()

    # URL かどうかを判定
    is_url = source.startswith("http://") or source.startswith("https://")

    if is_url:
        # URL からダウンロード
        response = requests.get(
            source,
            timeout=60.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        response.raise_for_status()

        # URL から拡張子を推測
        parsed_url = urlparse(source)
        url_path = parsed_url.path
        suffix = Path(url_path).suffix or ".pdf"  # デフォルトは PDF

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(response.content)
            temp_path = f.name

        try:
            result = md.convert(temp_path)
            return result.text_content
        finally:
            Path(temp_path).unlink(missing_ok=True)
    else:
        # ローカルファイル
        file_path = Path(source)
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {source}")

        result = md.convert(str(file_path))
        return result.text_content
