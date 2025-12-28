"""Filename generation utilities"""

import re
from datetime import datetime


def generate_download_filename(title: str, created_at: datetime) -> str:
    """
    Generate a safe filename for manga download.

    Format: manganize_{datetime}_{title}.png
    - datetime: YYYYMMDD_HHMMSS format
    - title: sanitized to remove special characters

    Args:
        title: Generated title (3-5 words)
        created_at: Creation timestamp

    Returns:
        Safe filename string

    Examples:
        >>> from datetime import datetime
        >>> dt = datetime(2025, 12, 28, 14, 30, 15)
        >>> generate_download_filename("Transformerアーキテクチャ", dt)
        'manganize_20251228_143015_Transformerアーキテクチャ.png'
        >>> generate_download_filename("Hello World! #test", dt)
        'manganize_20251228_143015_Hello_World_test.png'
    """
    # Format datetime
    dt_str = created_at.strftime("%Y%m%d_%H%M%S")

    # Sanitize title: replace non-alphanumeric chars with underscore
    # Keep Japanese characters, English alphanumeric, and underscores
    safe_title = re.sub(r"[^\w\s-]", "_", title)
    # Replace spaces with underscores
    safe_title = re.sub(r"[\s]+", "_", safe_title)
    # Remove multiple consecutive underscores
    safe_title = re.sub(r"_+", "_", safe_title)
    # Trim to max 50 chars
    safe_title = safe_title[:50].strip("_")

    return f"manganize_{dt_str}_{safe_title}.png"
