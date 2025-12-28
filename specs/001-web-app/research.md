# Research: Manganize Web App

**Created**: 2025-12-27
**Purpose**: 技術選択の根拠とベストプラクティスの調査結果

## 技術スタック決定

### HTMX パターン

**Decision**: HTMX 2.0 を使用してサーバーサイドレンダリング + 動的 UI 更新を実現

**Rationale**:
- SPA の複雑性（React/Vue の状態管理、ビルドツール、npm パッケージ管理）を回避
- Python エコシステムに統一（フロントエンド/バックエンド両方を Python で記述）
- Jinja2 テンプレートで SSR を行い、HTMX 属性で部分的な DOM 更新を実現
- 既存の manganize コア（Python/LangGraph）との統合が自然

**Alternatives considered**:
- Next.js + React: 過剰に複雑、JavaScript エコシステムの導入が必要
- Vanilla JavaScript + Fetch API: HTMX が提供する宣言的な API がより保守しやすい
- Streamlit: Web アプリとしての柔軟性に欠ける、カスタマイズが困難

### HTMX ベストプラクティス

**Progress Updates with SSE**:
```html
<!-- SSE による進捗更新 -->
<div hx-ext="sse" sse-connect="/api/generate/{id}/stream" sse-swap="message">
  <div id="progress-area">
    <!-- SSE イベントが到着するたびに更新される -->
  </div>
</div>
```

**Infinite Scroll**:
```html
<!-- 履歴一覧の無限スクロール -->
<div id="history-list">
  {% for item in history %}
  <div class="history-item">...</div>
  {% endfor %}
  <button hx-get="/api/history?page={{ next_page }}"
          hx-target="#history-list"
          hx-swap="beforeend"
          hx-trigger="revealed">
    もっと見る
  </button>
</div>
```

**Form Submission with Validation**:
```html
<!-- フォーム送信後にパーシャル更新 -->
<form hx-post="/api/generate"
      hx-target="#result-area"
      hx-indicator="#loading">
  <textarea name="topic"></textarea>
  <button type="submit">生成</button>
</form>
```

### FastAPI + Jinja2 統合

**Decision**: FastAPI で Jinja2 テンプレートをレンダリングし、HTML レスポンスと JSON レスポンスを使い分ける

**Rationale**:
- ページ全体 → Jinja2 テンプレートで SSR
- HTMX パーシャル → 小さな HTML スニペットを返す
- API エンドポイント → JSON で返す（ダウンロード、削除など）

**Pattern**:
```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
templates = Jinja2Templates(directory="web/templates")

# ページ全体をレンダリング
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# HTMX パーシャルを返す
@app.get("/api/history", response_class=HTMLResponse)
async def history_partial(request: Request, page: int = 1):
    items = await get_history(page)
    return templates.TemplateResponse("partials/history_list.html", {
        "request": request,
        "history": items
    })
```

### SSE (Server-Sent Events) パターン

**Decision**: sse-starlette を使用して FastAPI で SSE を実装

**Rationale**:
- WebSocket よりシンプル（一方向通信で十分）
- HTMX の `hx-ext="sse"` と統合が容易
- 自動再接続機能が標準搭載

**Pattern**:
```python
from sse_starlette.sse import EventSourceResponse

@app.get("/api/generate/{id}/stream")
async def generate_stream(id: str):
    async def event_generator():
        # 進捗状態を yield で返す
        yield {"event": "progress", "data": "<div>リサーチ中...</div>"}
        yield {"event": "progress", "data": "<div>シナリオ作成中...</div>"}
        yield {"event": "complete", "data": "<div>完了</div>"}

    return EventSourceResponse(event_generator())
```

### TailwindCSS セットアップ

**Decision**: Standalone CLI でビルド、ウォッチモードで開発

**Rationale**:
- Node.js 環境不要（standalone binary を使用）
- `npx tailwindcss` で簡単にビルド可能
- JIT モードでファイルサイズ最小化

**Configuration**:
```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./web/templates/**/*.html",
    "./web/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        kirara: {
          pink: '#FFB6C1',
          blue: '#87CEEB',
          yellow: '#FFFACD',
        }
      }
    }
  }
}
```

**Build Commands**:
```bash
# 開発時（ウォッチモード）
npx tailwindcss -i ./web/static/css/input.css -o ./web/static/css/output.css --watch

# 本番ビルド
npx tailwindcss -i ./web/static/css/input.css -o ./web/static/css/output.css --minify
```

### データベース設計

**Decision**: SQLAlchemy 2.0 (async) + aiosqlite (開発) / asyncpg (本番)

**Rationale**:
- FastAPI は非同期フレームワークなので async DB アクセスが推奨
- SQLAlchemy 2.0 の Mapped 型注釈で型安全性を確保
- SQLite (開発) → PostgreSQL (本番) へのマイグレーションが容易

**Pattern**:
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Async engine
engine = create_async_engine("sqlite+aiosqlite:///./data.db")

class Base(DeclarativeBase):
    pass

class GenerationHistory(Base):
    __tablename__ = "generation_history"

    id: Mapped[str] = mapped_column(primary_key=True)
    input_topic: Mapped[str]
    generated_title: Mapped[str]
    # ...
```

### ManganizeAgent 統合

**Decision**: GeneratorService でラップし、進捗コールバックを SSE に変換

**Rationale**:
- 既存の manganize コアエージェントを変更せず、ラッパーで適応
- LangGraph の stream イベントを FastAPI の SSE にマッピング
- バックグラウンドタスクで生成処理を実行

**Pattern**:
```python
import asyncio
from manganize.agents import ManganizeAgent

class GeneratorService:
    def __init__(self):
        self.agent = ManganizeAgent()
        self._active_generations: dict[str, asyncio.Queue] = {}

    async def start_generation(self, gen_id: str, topic: str, character: str):
        queue = asyncio.Queue()
        self._active_generations[gen_id] = queue

        # バックグラウンドで実行
        asyncio.create_task(self._run_generation(gen_id, topic, character, queue))

    async def get_progress_stream(self, gen_id: str):
        queue = self._active_generations.get(gen_id)
        if not queue:
            raise ValueError("Generation not found")

        while True:
            event = await queue.get()
            if event["type"] == "complete":
                break
            yield event
```

### タイトル生成

**Decision**: LLM (Gemini Flash) で 3-5 単語の短いタイトルを生成

**Rationale**:
- ファイル名として適切な長さ（30文字以内）
- ユーザー入力を要約することで内容を簡潔に表現
- 失敗時は日時のみをフォールバック

**Prompt Pattern**:
```python
title_prompt = f"""
以下のトピックから、3-5単語の短いタイトルを生成してください。
ファイル名として使用されるため、英数字、ひらがな、カタカナ、漢字のみを使用してください。

トピック: {topic}

条件:
- 3-5単語以内
- 特殊文字（/, \\, :, *, ?, ", <, >, |）を含めない
- スペースは使用可（アンダースコアに置換される）

タイトルのみを出力してください。
"""
```

### ファイルアップロード

**Decision**: python-multipart + markitdown でファイル読み取り

**Rationale**:
- `.txt`, `.pdf`, `.md` 形式をサポート
- markitdown で PDF をテキスト抽出
- 10MB サイズ制限

**Pattern**:
```python
from fastapi import UploadFile, File
from markitdown import MarkItDown

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(400, "File too large")

    if file.content_type not in ["text/plain", "text/markdown", "application/pdf"]:
        raise HTTPException(400, "Unsupported file type")

    content = await file.read()

    if file.content_type == "application/pdf":
        md = MarkItDown()
        text = md.convert(content).text_content
    else:
        text = content.decode("utf-8")

    return {"text": text}
```

## セキュリティ考慮事項

### 入力バリデーション

- トピック長: 最大 10,000 文字（Pydantic で検証）
- ファイルサイズ: 10MB 以下
- ファイル形式: MIME type チェック
- キャラクター名: 英数字とアンダースコアのみ

### CSRF 対策

FastAPI の CSRF ミドルウェアを使用（将来的に認証を追加する場合に備える）

### レート制限

slowapi を使用して 10 リクエスト/分/IP の制限を実装

## パフォーマンス最適化

### 画像サムネイル生成

Pillow で 200x200 のサムネイルを生成し、履歴一覧のロードを高速化

### データベースインデックス

- `generation_history.created_at` にインデックス（履歴表示の高速化）
- `characters.name` にユニーク制約 + インデックス

### 静的ファイル配信

FastAPI の StaticFiles で配信（開発環境）、nginx で配信（本番環境）

## 開発環境セットアップ

### 必要なツール

- Python 3.13+
- uv（パッケージ管理）
- Node.js（TailwindCSS ビルド用、または standalone binary）
- ty（型チェック）
- ruff（リント・フォーマット）

### 起動手順

```bash
# 1. 依存関係インストール
uv sync

# 2. TailwindCSS ビルド（別ターミナル）
npx tailwindcss -i ./web/static/css/input.css -o ./web/static/css/output.css --watch

# 3. FastAPI 起動
uv run uvicorn web.main:app --reload --port 8000
```

## 未解決の問題

該当なし - すべての技術選択が完了
