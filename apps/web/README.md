# manganize-web

manganize のための Web アプリケーションパッケージ。FastAPI + HTMX + TailwindCSS で構築されています。

## 概要

ユーザーがブラウザからトピックを入力すると、`manganize-core` のエージェントを使ってマンガ画像を生成するWebアプリケーションです。

- **リアルタイム進捗表示**: SSE（Server-Sent Events）で生成進捗をリアルタイム通知
- **履歴管理**: 過去の生成履歴を閲覧・ダウンロード
- **キャラクター管理**: 使用するキャラクターをカスタマイズ可能

## 技術スタック

| 技術 | 用途 |
|------|------|
| **FastAPI** | Web フレームワーク |
| **Uvicorn** | ASGI サーバー |
| **SQLAlchemy** | ORM（非同期対応） |
| **Alembic** | データベースマイグレーション |
| **Jinja2** | テンプレートエンジン |
| **HTMX** | フロントエンドの動的更新（SPAなし） |
| **TailwindCSS 4.x** | スタイリング |
| **SSE (sse-starlette)** | リアルタイム通知 |
| **SlowAPI** | レート制限 |

## ディレクトリ構成

```
manganize_web/
├── main.py                 # FastAPI アプリケーションのエントリーポイント
├── config.py               # 環境変数と設定管理
├── api/                    # API エンドポイント
│   ├── generation.py       # 生成API（POST /api/generate, SSE /api/generate/stream）
│   ├── history.py          # 履歴API（GET /api/history）
│   └── character.py        # キャラクターAPI
├── models/                 # SQLAlchemy モデル
│   ├── database.py         # DB エンジン設定
│   ├── generation.py       # 生成履歴モデル
│   └── character.py        # キャラクターモデル
├── repositories/           # データアクセス層
├── schemas/                # Pydantic スキーマ（リクエスト/レスポンス）
├── services/               # ビジネスロジック
│   ├── generator.py        # 生成サービス（manganize-core との連携）
│   └── history.py          # 履歴サービス
├── templates/              # Jinja2 テンプレート
│   ├── base.html
│   ├── index.html          # トップページ
│   ├── history.html        # 履歴ページ
│   └── partials/           # HTMX で使用する部分テンプレート
└── static/
    ├── css/                # TailwindCSS
    └── js/                 # クライアントサイドスクリプト
```

## セットアップ

### 1. データベースのマイグレーション

```bash
# ルートディレクトリから実行
uv run alembic upgrade head
```

### 2. デフォルトキャラクターのシード

```bash
uv run python -m manganize_web.models.seed
```

### 3. TailwindCSS のビルド

```bash
# 開発モード（watch）
npx @tailwindcss/cli -i apps/web/manganize_web/static/css/input.css -o apps/web/manganize_web/static/css/output.css --watch

# 本番ビルド
npx @tailwindcss/cli -i apps/web/manganize_web/static/css/input.css -o apps/web/manganize_web/static/css/output.css --minify
# または
task build:tailwindcss
```

## 開発サーバーの起動

```bash
# ルートディレクトリから実行
task dev
# または
uv run fastapi dev apps/web/manganize_web/main.py --reload-dir apps/web --reload-dir packages/core
```

http://127.0.0.1:8000 にアクセス

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|-------|------|------------|
| `GOOGLE_API_KEY` | Google Generative AI の API キー | - |
| `DATABASE_URL` | データベース URL | `sqlite+aiosqlite:///./manganize.db` |
| `CORS_ORIGINS` | CORS 許可オリジン | `["http://localhost:8000"]` |
| `RATE_LIMIT_PER_MINUTE` | レート制限（回/分） | `10` |

## API エンドポイント

### 生成 API

```bash
# 生成リクエスト（非同期）
POST /api/generate
Content-Type: application/json

{
  "topic": "Transformerアーキテクチャについて",
  "character": "kurage_chan"
}

# 進捗ストリーム（SSE）
GET /api/generate/stream/{generation_id}
Accept: text/event-stream
```

### 履歴 API

```bash
# 履歴一覧
GET /api/history?limit=10&offset=0

# 画像ダウンロード
GET /api/history/{generation_id}/image
```

## 開発

```bash
# リント
uv run ruff check packages/web/manganize_web

# フォーマット
uv run ruff format packages/web/manganize_web

# 型チェック
uv run ty packages/web/manganize_web
```
