"""Google AI backend detection and configuration.

Supports two backends:
- Gemini Developer API: requires GOOGLE_API_KEY
- Vertex AI: requires GOOGLE_CLOUD_PROJECT (or GOOGLE_GENAI_USE_VERTEXAI=true)
  with Application Default Credentials (gcloud auth application-default login)
"""

import os
from enum import StrEnum


class Backend(StrEnum):
    GEMINI = "gemini"
    VERTEX = "vertex"


def detect_backend() -> Backend:
    """Detect which Google AI backend to use based on environment variables.

    Priority:
    1. GOOGLE_API_KEY set → Gemini Developer API
    2. GOOGLE_CLOUD_PROJECT or GOOGLE_GENAI_USE_VERTEXAI set → Vertex AI
    3. Neither → raises EnvironmentError with actionable message
    """
    if os.environ.get("GOOGLE_API_KEY"):
        return Backend.GEMINI
    if os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get(
        "GOOGLE_GENAI_USE_VERTEXAI"
    ):
        return Backend.VERTEX
    raise EnvironmentError(
        "Google AI の認証情報が設定されていません。\n"
        "Gemini API を使う場合: GOOGLE_API_KEY を設定してください。\n"
        "Vertex AI を使う場合: GOOGLE_CLOUD_PROJECT を設定し、"
        "`gcloud auth application-default login` を実行してください。"
    )


def configure_backend() -> Backend:
    """Detect backend and configure the SDK environment. Returns detected backend.

    Side effect: sets GOOGLE_GENAI_USE_VERTEXAI=true when Vertex AI is detected,
    so that genai.Client() automatically uses Vertex AI.
    """
    backend = detect_backend()
    if backend == Backend.VERTEX:
        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
    return backend


def get_langchain_model(base_name: str, backend: Backend) -> str:
    """Return the LangChain model string for the given backend.

    Args:
        base_name: Model name without provider prefix (e.g. "gemini-2.5-pro")
        backend: Detected backend

    Returns:
        Full model string (e.g. "google_genai:gemini-2.5-pro" or "vertexai:gemini-2.5-pro")
    """
    prefix = "google_genai" if backend == Backend.GEMINI else "google_vertexai"
    return f"{prefix}:{base_name}"
