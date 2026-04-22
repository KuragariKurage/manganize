"""Image generation dispatch for manga pipeline.

Supports Google Gemini and OpenAI gpt-image-2.

Provider is selected via CLI flag (highest priority) or the ``IMAGE_PROVIDER``
environment variable, defaulting to Google. See :func:`resolve_image_provider`.
"""

import base64
import os
from enum import StrEnum

from google import genai
from google.genai import types

from manganize_core.backend import configure_backend
from manganize_core.character import BaseCharacter
from manganize_core.prompts import get_image_generation_system_prompt

_GOOGLE_IMAGE_MODEL = "gemini-3-pro-image-preview"
_GOOGLE_ASPECT_RATIO = "9:16"
_GOOGLE_IMAGE_SIZE = "2K"

# OpenAI gpt-image-2 only supports 1:1, 2:3, and 3:2. 1024x1536 is the
# closest match to the 9:16 portrait used by the Google path.
_OPENAI_IMAGE_MODEL_DEFAULT = "gpt-image-2"
_OPENAI_IMAGE_SIZE = "1024x1536"
_OPENAI_IMAGE_QUALITY = "high"


class ImageProvider(StrEnum):
    GOOGLE = "google"
    OPENAI = "openai"


def resolve_image_provider(cli_flag: str | None = None) -> ImageProvider:
    """Resolve the image provider.

    Precedence: ``cli_flag`` > ``IMAGE_PROVIDER`` env var > default (Google).
    Raises ``ValueError`` if the value is not a known provider.
    """
    raw = cli_flag or os.environ.get("IMAGE_PROVIDER") or ImageProvider.GOOGLE.value
    try:
        return ImageProvider(raw.lower())
    except ValueError:
        valid = [p.value for p in ImageProvider]
        raise ValueError(
            f"不明な画像プロバイダー: {raw!r}。有効な値: {valid}"
        ) from None


def generate_image(
    content: str,
    character: BaseCharacter,
    provider: ImageProvider,
) -> bytes:
    """Dispatch image generation to the specified provider."""
    if provider == ImageProvider.OPENAI:
        return _generate_openai(content, character)
    return _generate_google(content, character)


def _generate_google(content: str, character: BaseCharacter) -> bytes:
    """Generate via Gemini gemini-3-pro-image-preview."""
    configure_backend()
    client = genai.Client()

    response = client.models.generate_content(
        model=_GOOGLE_IMAGE_MODEL,
        contents=[
            types.Part.from_bytes(
                data=character.get_portrait_bytes(), mime_type="image/png"
            ),
            types.Part.from_bytes(
                data=character.get_full_body_bytes(), mime_type="image/png"
            ),
            types.Part.from_text(text=f"脚本:\n{content}"),
        ],
        config=types.GenerateContentConfig(
            system_instruction=get_image_generation_system_prompt(character),
            image_config=types.ImageConfig(
                aspect_ratio=_GOOGLE_ASPECT_RATIO,
                image_size=_GOOGLE_IMAGE_SIZE,
            ),
            tools=[{"google_search": {}}],
        ),
    )

    if response.parts is None:
        raise RuntimeError("Google画像生成: レスポンスにパーツがありません")

    image_parts = [p for p in response.parts if p.inline_data]
    if not image_parts or not image_parts[0].inline_data:
        raise RuntimeError("Google画像生成: 画像パーツが返されませんでした")

    image_data = image_parts[0].inline_data.data
    if image_data is None:
        raise RuntimeError("Google画像生成: inline_data が空でした")

    return image_data


def _generate_openai(content: str, character: BaseCharacter) -> bytes:
    """Generate via OpenAI gpt-image-2 using the ``images.edit`` endpoint.

    Character portrait and full-body images are passed as multimodal references
    so the model can match the character's appearance, mirroring the Google path.
    """
    from openai import OpenAI

    model = os.environ.get("OPENAI_IMAGE_MODEL", _OPENAI_IMAGE_MODEL_DEFAULT)
    client = OpenAI()

    prompt = get_image_generation_system_prompt(character) + f"\n\n脚本:\n{content}"

    # gpt-image-* returns b64_json by default; ``response_format`` and ``n`` are
    # rejected by the API so we omit them.
    response = client.images.edit(
        model=model,
        image=[
            ("portrait.png", character.get_portrait_bytes(), "image/png"),
            ("full_body.png", character.get_full_body_bytes(), "image/png"),
        ],
        prompt=prompt,
        size=_OPENAI_IMAGE_SIZE,
        quality=_OPENAI_IMAGE_QUALITY,
    )

    if not response.data or not response.data[0].b64_json:
        raise RuntimeError("OpenAI画像生成: 画像データが返されませんでした")

    return base64.b64decode(response.data[0].b64_json)
