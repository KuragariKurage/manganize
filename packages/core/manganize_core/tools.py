import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from google import genai
from google.genai import types
from langchain.tools import tool
from markitdown import MarkItDown
from PIL import Image
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from manganize_core.character import BaseCharacter
from manganize_core.prompts import (
    get_image_generation_system_prompt,
    get_image_revision_system_prompt,
)

REVISION_IMAGE_TARGET_BYTES = 1_500_000
REVISION_IMAGE_MIN_QUALITY = 65
REVISION_IMAGE_QUALITY_STEPS = (90, 85, 80, 75, 70, 65)
REVISION_IMAGE_MAX_LONG_EDGE = 2048


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


def _format_revision_payload(revision_payload: dict[str, Any]) -> str:
    """Format revision payload into a stable text block for the model."""
    global_instruction = (revision_payload.get("global_instruction") or "").strip()
    edits: list[dict[str, Any]] = revision_payload.get("edits", []) or []

    lines: list[str] = []
    if global_instruction:
        lines.append(f"全体指示: {global_instruction}")
    else:
        lines.append("全体指示: なし")

    for index, edit in enumerate(edits, start=1):
        target = edit.get("target", {})
        kind = target.get("kind", "unknown")
        if kind == "point":
            target_desc = (
                "point("
                f"x={target.get('x')}, y={target.get('y')}, "
                f"radius={target.get('radius', 0.04)})"
            )
        elif kind == "box":
            target_desc = (
                "box("
                f"x={target.get('x')}, y={target.get('y')}, "
                f"w={target.get('w')}, h={target.get('h')})"
            )
        else:
            target_desc = str(target)

        instruction = (edit.get("instruction") or "").strip()
        edit_type = edit.get("edit_type", "auto")
        expected_text = (edit.get("expected_text") or "").strip()

        lines.append(f"[Edit {index}]")
        lines.append(f"- target: {target_desc}")
        lines.append(f"- edit_type: {edit_type}")
        lines.append(f"- instruction: {instruction}")
        if expected_text:
            lines.append(f"- expected_text: {expected_text}")

    return "\n".join(lines)


def _prepare_revision_base_image(base_image: bytes) -> tuple[bytes, str]:
    """
    Prepare revision base image for model input with lightweight compression.

    This reduces payload size for revision requests while keeping quality high.
    Falls back to the original PNG bytes if conversion fails.
    """
    try:
        image = Image.open(BytesIO(base_image))

        # Limit extreme dimensions while keeping aspect ratio.
        long_edge = max(image.width, image.height)
        if long_edge > REVISION_IMAGE_MAX_LONG_EDGE:
            scale = REVISION_IMAGE_MAX_LONG_EDGE / float(long_edge)
            resized = image.resize(
                (
                    max(1, int(image.width * scale)),
                    max(1, int(image.height * scale)),
                ),
                Image.Resampling.LANCZOS,
            )
            image = resized

        # JPEG does not support alpha; composite onto white if needed.
        if image.mode in ("RGBA", "LA") or (
            image.mode == "P" and "transparency" in image.info
        ):
            background = Image.new("RGB", image.size, (255, 255, 255))
            alpha = image.getchannel("A") if "A" in image.getbands() else None
            rgb_image = image.convert("RGB")
            if alpha:
                background.paste(rgb_image, mask=alpha)
                image = background
            else:
                image = rgb_image
        elif image.mode != "RGB":
            image = image.convert("RGB")

        best_data: bytes | None = None
        for quality in REVISION_IMAGE_QUALITY_STEPS:
            buffer = BytesIO()
            image.save(
                buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            candidate = buffer.getvalue()
            best_data = candidate
            if len(candidate) <= REVISION_IMAGE_TARGET_BYTES:
                return candidate, "image/jpeg"

        # If still large, return the best compressed JPEG attempt.
        if best_data is not None and len(best_data) < len(base_image):
            return best_data, "image/jpeg"
    except Exception:
        # Fallback: keep original bytes and MIME type.
        pass

    return base_image, "image/png"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=15))
def edit_manga_image(
    content: str,
    base_image: bytes,
    revision_payload: dict[str, Any],
    character: BaseCharacter,
) -> bytes | None:
    """マンガ画像の部分修正を行うエージェントです。

    Args:
        content: 元トピックのテキスト
        base_image: 親画像のバイナリ
        revision_payload: 修正指示（point/box + instruction）
        character: 使用するキャラクター情報

    Returns:
        修正後の画像バイトデータ（PNG形式）、失敗時はNone
    """
    try:
        client = genai.Client()
        revision_text = _format_revision_payload(revision_payload)
        prepared_base_image, base_image_mime_type = _prepare_revision_base_image(
            base_image
        )

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
                types.Part.from_bytes(
                    data=prepared_base_image,
                    mime_type=base_image_mime_type,
                ),
                types.Part.from_text(
                    text=(f"元トピック:\n{content}\n\n修正指示:\n{revision_text}")
                ),
            ],
            config=types.GenerateContentConfig(
                system_instruction=get_image_revision_system_prompt(character),
                image_config=types.ImageConfig(aspect_ratio="9:16", image_size="2K"),
                tools=[{"google_search": {}}],
            ),
        )

        if response.parts is None:
            return None

        image_parts = [part for part in response.parts if part.inline_data]
        if image_parts:
            image_data = (
                image_parts[0].inline_data.data if image_parts[0].inline_data else None
            )
            if image_data:
                return image_data
    except Exception as e:
        raise RuntimeError(f"画像修正に失敗しました: {e}") from e

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
