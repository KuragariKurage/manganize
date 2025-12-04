import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from google import genai
from google.genai import types
from langchain.tools import tool
from markitdown import MarkItDown
from playwright.sync_api import sync_playwright

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
