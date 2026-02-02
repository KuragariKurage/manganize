"""Image processing utilities for character reference images"""

import io
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

# Maximum file size: 5MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024

# Allowed MIME types
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg"}

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# Get project root (characters directory is at project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded image file.

    Args:
        file: Uploaded file to validate

    Raises:
        HTTPException: If validation fails
    """
    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が不正です")

    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="PNG または JPEG 形式の画像をアップロードしてください。",
        )

    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="PNG または JPEG 形式の画像をアップロードしてください。",
        )

    # Check file size
    if hasattr(file, "size") and file.size is not None:
        if file.size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"画像ファイルが大きすぎます。{MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB以下にしてください。",
            )


async def save_character_image(
    character_name: str,
    image_type: str,
    image_file: UploadFile,
) -> str:
    """
    Save character reference image to disk.

    Args:
        character_name: Character name
        image_type: Image type ('portrait' or 'full_body')
        image_file: Uploaded image file

    Returns:
        Relative path to saved image

    Raises:
        HTTPException: If validation or save fails
    """
    # Validate file
    validate_image_file(image_file)

    # Read file content
    content = await image_file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"画像ファイルが大きすぎます。{MAX_IMAGE_SIZE / 1024 / 1024:.0f}MB以下にしてください。",
        )

    # Verify it's a valid image using Pillow
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()  # Verify that it's actually an image
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="画像ファイルが壊れています。",
        )

    # Determine file extension
    ext = Path(image_file.filename).suffix.lower()

    # Create character assets directory
    assets_dir = PROJECT_ROOT / "characters" / character_name / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Save image with fixed filename based on type
    filename = f"{image_type}{ext}"
    image_path = assets_dir / filename

    # Write image to disk
    with open(image_path, "wb") as f:
        f.write(content)

    # Return relative path from project root
    relative_path = str(image_path.relative_to(PROJECT_ROOT))
    return relative_path


def get_character_image_path(character_name: str, image_type: str) -> Path | None:
    """
    Get path to character reference image.

    Args:
        character_name: Character name
        image_type: Image type ('portrait' or 'full_body')

    Returns:
        Path to image file if exists, None otherwise
    """
    assets_dir = PROJECT_ROOT / "characters" / character_name / "assets"

    # Try both .png and .jpg/.jpeg extensions
    for ext in [".png", ".jpg", ".jpeg"]:
        image_path = assets_dir / f"{image_type}{ext}"
        if image_path.exists():
            return image_path

    return None


async def load_character_image(character_name: str, image_type: str) -> bytes:
    """
    Load character reference image from disk.

    Args:
        character_name: Character name
        image_type: Image type ('portrait' or 'full_body')

    Returns:
        Image bytes

    Raises:
        HTTPException: If image not found
    """
    image_path = get_character_image_path(character_name, image_type)

    if not image_path:
        raise HTTPException(status_code=404, detail="画像が見つかりません")

    try:
        with open(image_path, "rb") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"画像の読み込み中にエラーが発生しました: {str(e)}",
        )


def delete_character_images(character_name: str) -> None:
    """
    Delete all character reference images.

    Args:
        character_name: Character name
    """
    assets_dir = PROJECT_ROOT / "characters" / character_name / "assets"

    if not assets_dir.exists():
        return

    # Delete all image files in assets directory
    for ext in [".png", ".jpg", ".jpeg"]:
        for image_type in ["portrait", "full_body"]:
            image_path = assets_dir / f"{image_type}{ext}"
            if image_path.exists():
                try:
                    image_path.unlink()
                except Exception:
                    # Ignore deletion errors (file may be in use, etc.)
                    pass

    # Try to delete assets directory if empty
    try:
        if assets_dir.exists() and not any(assets_dir.iterdir()):
            assets_dir.rmdir()
    except Exception:
        pass

    # Try to delete character directory if empty
    character_dir = assets_dir.parent
    try:
        if character_dir.exists() and not any(character_dir.iterdir()):
            character_dir.rmdir()
    except Exception:
        pass
