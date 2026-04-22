import shutil
import subprocess
import tempfile
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pathspec
import requests
from git import InvalidGitRepositoryError, Repo
from google import genai
from google.genai import types
from langchain.tools import tool
from markitdown import MarkItDown
from PIL import Image
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from manganize_core.backend import configure_backend
from manganize_core.character import BaseCharacter
from manganize_core.image_generation import (
    ImageProvider,
    generate_image,
    resolve_image_provider,
)
from manganize_core.prompts import get_image_revision_system_prompt

REVISION_IMAGE_TARGET_BYTES = 1_500_000
REVISION_IMAGE_MIN_QUALITY = 65
REVISION_IMAGE_QUALITY_STEPS = (90, 85, 80, 75, 70, 65)
REVISION_IMAGE_MAX_LONG_EDGE = 2048


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=15))
def generate_manga_image(
    content: str,
    character: BaseCharacter,
    provider: ImageProvider | None = None,
) -> bytes | None:
    """マンガの作画を行うエージェントです。

    指定されたコンテンツとキャラクターに基づいて、選択されたプロバイダー
    （Google Gemini または OpenAI gpt-image-2）で漫画風の画像を生成します。
    生成された画像はPNG形式のバイト列として返されます。

    Args:
        content: 画像生成のためのコンテンツ。漫画化したいテキストやストーリーの説明を含む。
        character: 使用するキャラクター情報
        provider: 使用する画像プロバイダー。``None`` の場合は ``IMAGE_PROVIDER``
            環境変数または既定値(Google)から解決する。

    Returns:
        生成された画像のバイトデータ（PNG形式）、失敗時はNone

    Example:
        >>> from manganize_core.character import KurageChan
        >>> character = KurageChan()
        >>> image_data = generate_manga_image("可愛い女の子が笑顔で挨拶している", character)
        >>> if image_data:
        >>>     image = Image.open(io.BytesIO(image_data))
        >>>     image.save("manga.png")
    """
    try:
        resolved_provider = provider or resolve_image_provider()
        return generate_image(content, character, resolved_provider)
    except RuntimeError:
        # Provider already raised with a clear Japanese message — pass through.
        raise
    except Exception as e:
        raise RuntimeError(f"画像生成に失敗しました: {e}") from e


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
        configure_backend()
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


# --- Repository exploration constants ---

REPO_MAX_FILE_BYTES = 100_000
REPO_MAX_TOTAL_BYTES = 1_000_000
REPO_TREE_MAX_DEPTH = 4
REPO_GIT_LOG_LIMIT = 30

SENSITIVE_PATTERNS = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "credentials*",
    "*secret*",
    "*.p12",
    "*.pfx",
]

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".webp",
    ".mp3",
    ".mp4",
    ".wav",
    ".avi",
    ".mov",
    ".mkv",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".pyc",
    ".pyo",
    ".so",
    ".dll",
    ".dylib",
    ".o",
    ".exe",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".pdf",
}


def _load_ignore_spec(repo_path: Path) -> pathspec.PathSpec:
    """Load .gitignore + built-in sensitive patterns into a single PathSpec."""
    gitignore = repo_path / ".gitignore"
    patterns: list[str] = []
    if gitignore.exists():
        patterns = gitignore.read_text(encoding="utf-8", errors="ignore").splitlines()
    # Always ignore .git directory and sensitive files
    patterns.append(".git/")
    patterns.extend(SENSITIVE_PATTERNS)
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def _build_directory_tree(repo_path: Path, ignore_spec: pathspec.PathSpec) -> str:
    """Build a directory tree string up to REPO_TREE_MAX_DEPTH."""
    lines: list[str] = [repo_path.name + "/"]

    def _walk(current: Path, prefix: str, depth: int) -> None:
        if depth >= REPO_TREE_MAX_DEPTH:
            return
        try:
            entries = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return

        visible: list[Path] = []
        for entry in entries:
            rel = str(entry.relative_to(repo_path))
            if entry.is_dir():
                rel += "/"
            if ignore_spec.match_file(rel):
                continue
            visible.append(entry)

        for i, entry in enumerate(visible):
            is_last = i == len(visible) - 1
            connector = "└── " if is_last else "├── "
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{connector}{entry.name}{suffix}")
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, depth + 1)

    _walk(repo_path, "", 0)
    return "\n".join(lines)


def _collect_language_stats(
    repo_path: Path, ignore_spec: pathspec.PathSpec
) -> dict[str, int]:
    """Count files by extension, ignoring gitignored and binary files."""
    counter: Counter[str] = Counter()
    for file in repo_path.rglob("*"):
        if not file.is_file():
            continue
        rel = str(file.relative_to(repo_path))
        if ignore_spec.match_file(rel):
            continue
        ext = file.suffix.lower()
        if ext in BINARY_EXTENSIONS or not ext:
            continue
        counter[ext] += 1
    return dict(counter.most_common(15))


def _analyze_git_history(repo: Repo) -> str:
    """Analyze recent git history and return a summary."""
    lines: list[str] = []
    commits = list(repo.iter_commits(max_count=REPO_GIT_LOG_LIMIT))
    if not commits:
        return "Git履歴なし（コミットが見つかりません）"

    lines.append(f"総コミット数（直近{REPO_GIT_LOG_LIMIT}件まで）: {len(commits)}")

    # Recent commits summary
    lines.append("\n### 直近のコミット")
    for commit in commits[:10]:
        date = commit.committed_datetime.strftime("%Y-%m-%d")
        msg = str(commit.message).strip().split("\n")[0][:80]
        lines.append(f"- `{date}` {msg}")

    # Hotspot analysis: files changed most frequently
    file_change_count: Counter[str] = Counter()
    for commit in commits:
        try:
            if commit.parents:
                diffs = commit.diff(commit.parents[0])
            else:
                diffs = commit.diff(None)
            for diff in diffs:
                path = diff.b_path or diff.a_path
                if path:
                    file_change_count[path] += 1
        except Exception:
            continue

    if file_change_count:
        lines.append("\n### ホットスポット（変更頻度の高いファイル）")
        for path, count in file_change_count.most_common(10):
            lines.append(f"- `{path}` ({count}回変更)")

    # Contributors
    authors: Counter[str] = Counter()
    for commit in commits:
        author_name = commit.author.name or "Unknown"
        authors[author_name] += 1
    if authors:
        lines.append("\n### コントリビューター")
        for author, count in authors.most_common(5):
            lines.append(f"- {author} ({count}コミット)")

    return "\n".join(lines)


def _read_key_files(repo_path: Path, ignore_spec: pathspec.PathSpec) -> str:
    """Read key project files (README, config, entry points)."""
    key_file_candidates = [
        "README.md",
        "README.rst",
        "README.txt",
        "README",
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "Makefile",
        "Taskfile.yml",
        "docker-compose.yml",
    ]
    lines: list[str] = []
    total_bytes = 0

    for name in key_file_candidates:
        fpath = repo_path / name
        if not fpath.exists() or not fpath.is_file():
            continue
        rel = str(fpath.relative_to(repo_path))
        if ignore_spec.match_file(rel):
            continue
        try:
            size = fpath.stat().st_size
            if size > REPO_MAX_FILE_BYTES:
                lines.append(f"\n### {name} (先頭のみ、{size}バイト)")
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :REPO_MAX_FILE_BYTES
                ]
            else:
                lines.append(f"\n### {name}")
                content = fpath.read_text(encoding="utf-8", errors="ignore")

            total_bytes += len(content.encode("utf-8"))
            if total_bytes > REPO_MAX_TOTAL_BYTES:
                lines.append("（合計サイズ上限に達したため省略）")
                break
            lines.append(f"```\n{content}\n```")
        except Exception:
            continue

    return "\n".join(lines) if lines else "主要ファイルが見つかりませんでした"


def _try_repomix(repo_path: Path) -> str | None:
    """Try to run repomix if available. Returns summary or None."""
    if not shutil.which("repomix"):
        return None
    try:
        result = subprocess.run(
            ["repomix", "--style", "markdown", "--output-show-line-numbers", "false"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(repo_path),
        )
        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            # Truncate if too large
            if len(output) > REPO_MAX_TOTAL_BYTES:
                return (
                    output[:REPO_MAX_TOTAL_BYTES]
                    + "\n\n（repomix出力が大きいため省略）"
                )
            return output
    except (subprocess.TimeoutExpired, Exception):
        pass
    return None


@tool
def explore_repository(path: str, focus: str = "") -> str:
    """ローカルのGitリポジトリまたはディレクトリを探索し、構造・履歴・コードの概要を返す。

    リポジトリの全体像を把握し、漫画のネタになる面白いポイントを
    見つけるために使用する。ディレクトリ構造、使用言語、Git履歴の
    ハイライト、主要ファイルの内容を分析する。

    Args:
        path: リポジトリのローカルパス（絶対パスまたは相対パス）
        focus: 特に注目したい観点（例: "アーキテクチャ", "Git履歴", "設計思想"）。
               空の場合は全体的な分析を行う。

    Returns:
        リポジトリ分析の結果（Markdown形式）
    """
    repo_path = Path(path).expanduser().resolve()
    if not repo_path.exists():
        return f"パスが見つかりません: {path}（パスを確認してください）"
    if not repo_path.is_dir():
        return f"ディレクトリではありません: {path}（ファイルではなくディレクトリを指定してください）"

    ignore_spec = _load_ignore_spec(repo_path)
    sections: list[str] = []

    # Header
    sections.append(f"# リポジトリ分析: {repo_path.name}")
    if focus:
        sections.append(f"注目観点: {focus}")

    # Directory tree
    try:
        sections.append("\n## ディレクトリ構造")
        sections.append(f"```\n{_build_directory_tree(repo_path, ignore_spec)}\n```")
    except Exception as e:
        sections.append(f"\n## ディレクトリ構造\n取得に失敗しました: {e}")

    # Language stats
    try:
        lang_stats = _collect_language_stats(repo_path, ignore_spec)
        if lang_stats:
            sections.append("\n## 使用言語・ファイル統計")
            for ext, count in lang_stats.items():
                sections.append(f"- `{ext}`: {count}ファイル")
    except Exception as e:
        sections.append(f"\n## 使用言語・ファイル統計\n取得に失敗しました: {e}")

    # Git history (if it's a git repo)
    try:
        repo = Repo(str(repo_path))
        sections.append("\n## Git履歴")
        sections.append(_analyze_git_history(repo))
    except InvalidGitRepositoryError:
        sections.append("\n## Git履歴")
        sections.append("Gitリポジトリではありません（Git履歴分析をスキップ）")
    except Exception as e:
        sections.append(f"\n## Git履歴\n取得に失敗しました: {e}")

    # Key project files
    try:
        sections.append("\n## 主要ファイル")
        sections.append(_read_key_files(repo_path, ignore_spec))
    except Exception as e:
        sections.append(f"\n## 主要ファイル\n取得に失敗しました: {e}")

    # Try repomix for additional context
    repomix_output = _try_repomix(repo_path)
    if repomix_output:
        sections.append("\n## Repomix 分析")
        sections.append(repomix_output)

    return "\n".join(sections)
