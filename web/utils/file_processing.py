"""File processing utilities for text extraction from uploaded files"""

import io
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, UploadFile

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".md", ".markdown"}


def validate_file_size(file: UploadFile) -> None:
    """
    Validate uploaded file size.

    Args:
        file: Uploaded file to validate

    Raises:
        HTTPException: If file size exceeds limit
    """
    # Try to get file size from content-length header
    if hasattr(file, "size") and file.size is not None:
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"ファイルサイズが大きすぎます。{MAX_FILE_SIZE / 1024 / 1024:.0f}MB以下にしてください。",
            )


def validate_file_type(filename: str) -> None:
    """
    Validate uploaded file type by extension.

    Args:
        filename: Name of the uploaded file

    Raises:
        HTTPException: If file type is not allowed
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"サポートされていないファイル形式です。{', '.join(ALLOWED_EXTENSIONS)} のいずれかをアップロードしてください。",
        )


async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extract text content from uploaded file.

    Uses markitdown for PDF extraction, direct read for text files.

    Args:
        file: Uploaded file to extract text from

    Returns:
        Extracted text content

    Raises:
        HTTPException: If text extraction fails
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が不正です")

    validate_file_type(file.filename)
    validate_file_size(file)

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"ファイルサイズが大きすぎます。{MAX_FILE_SIZE / 1024 / 1024:.0f}MB以下にしてください。",
        )

    # Reset file position for potential reuse
    await file.seek(0)

    ext = Path(file.filename).suffix.lower()

    try:
        # Plain text files (.txt, .md, .markdown)
        if ext in {".txt", ".md", ".markdown"}:
            return content.decode("utf-8", errors="replace")

        # PDF files - use markitdown
        elif ext == ".pdf":
            # Lazy import to speed up server startup
            from markitdown import MarkItDown

            md = MarkItDown()

            # Create a BytesIO object that acts like a file
            file_like = io.BytesIO(content)

            # markitdown expects a file path, but we can trick it with a file-like object
            # by creating a temporary named tuple with file and name attributes
            class FileWrapper:
                def __init__(self, file_obj: BinaryIO, filename: str):
                    self.file = file_obj
                    self.name = filename

            wrapper = FileWrapper(file_like, file.filename)

            # Extract text using markitdown
            result = md.convert_stream(wrapper.file, file_extension=ext)

            if not result or not result.text_content:
                raise HTTPException(
                    status_code=400,
                    detail="PDFからテキストを抽出できませんでした",
                )

            return result.text_content.strip()

        else:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です: {ext}",
            )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="ファイルのエンコーディングが不正です。UTF-8形式のファイルをアップロードしてください。",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ファイルの処理中にエラーが発生しました: {str(e)}",
        )
