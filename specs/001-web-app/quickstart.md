# Quickstart: Manganize Web App

**Purpose**: 開発者がWeb アプリケーションをローカル環境で起動するための手順

## 前提条件

- Python 3.13 以上
- uv（パッケージ管理）
- Node.js 18 以上（TailwindCSS ビルド用）または TailwindCSS standalone binary
- Google API Key（Gemini LLM使用のため）

## セットアップ手順

### 1. 依存関係のインストール

```bash
# プロジェクトルートに移動
cd /path/to/manganize

# 依存関係をインストール
uv sync

# (オプション) Playwright のブラウザをインストール（既存のコアエージェント用）
uv run playwright install chromium
```

### 2. 環境変数の設定

```bash
# .env ファイルを作成
cat > .env << 'EOF'
# Google Gemini API Key (必須)
GOOGLE_API_KEY=your-api-key-here

# データベースURL (オプション、デフォルトは SQLite)
DATABASE_URL=sqlite+aiosqlite:///./manganize.db

# FastAPI 設定
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
EOF

# API キーを取得: https://aistudio.google.com/app/apikey
```

### 3. データベースの初期化

```bash
# マイグレーションを実行
uv run alembic upgrade head

# デフォルトキャラクター（くらげ）を投入
uv run python -m web.models.seed
```

### 4. TailwindCSS のビルド

#### Option A: Node.js を使用

```bash
# TailwindCSS をインストール（初回のみ）
npm install -D tailwindcss

# ウォッチモードでビルド（別ターミナルで実行）
npx tailwindcss -i ./web/static/css/input.css \
                -o ./web/static/css/output.css \
                --watch
```

#### Option B: Standalone Binary を使用

```bash
# Standalone binary をダウンロード（初回のみ）
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64
chmod +x tailwindcss-linux-x64

# ウォッチモードでビルド（別ターミナルで実行）
./tailwindcss-linux-x64 -i ./web/static/css/input.css \
                         -o ./web/static/css/output.css \
                         --watch
```

### 5. FastAPI サーバーの起動

```bash
# 開発サーバーを起動（ホットリロード有効）
uv run uvicorn web.main:app --reload --port 8000 --host 0.0.0.0
```

### 6. ブラウザでアクセス

```
http://localhost:8000
```

## ディレクトリ構成の確認

起動前に以下のファイル/ディレクトリが存在することを確認：

```
web/
├── __init__.py
├── main.py              # FastAPI アプリケーション
├── config.py            # 設定ファイル
├── api/                 # API routes
├── models/              # Database models
├── schemas/             # Pydantic schemas
├── services/            # Business logic
├── templates/           # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── history.html
│   ├── character.html
│   └── partials/
└── static/              # Static assets
    ├── css/
    │   ├── input.css    # TailwindCSS input
    │   └── output.css   # TailwindCSS output (generated)
    ├── js/
    │   └── htmx.min.js
    └── images/
```

## 開発ワークフロー

### コードの変更

1. Python コードを変更 → uvicorn が自動リロード
2. Jinja2 テンプレートを変更 → ブラウザをリフレッシュ
3. TailwindCSS クラスを追加 → 自動ビルド（ウォッチモード）

### 品質チェック

```bash
# リント
uv run ruff check .

# フォーマット
uv run ruff format .

# 型チェック
uv run ty check
```

### テスト実行

```bash
# すべてのテストを実行
uv run pytest

# 特定のテストファイルのみ
uv run pytest tests/test_api/test_generation.py

# カバレッジレポート
uv run pytest --cov=web --cov-report=html
```

## トラブルシューティング

### "Google API Key not found" エラー

`.env` ファイルに `GOOGLE_API_KEY` が設定されているか確認：

```bash
cat .env | grep GOOGLE_API_KEY
```

### TailwindCSS がビルドされない

`tailwind.config.js` が存在するか確認：

```bash
ls tailwind.config.js
```

存在しない場合は作成：

```javascript
module.exports = {
  content: [
    "./web/templates/**/*.html",
    "./web/static/js/**/*.js",
  ],
  theme: {
    extend: {}
  },
  plugins: [],
}
```

### データベースマイグレーションエラー

データベースをリセット：

```bash
rm -f manganize.db
uv run alembic upgrade head
uv run python -m web.models.seed
```

### ポート 8000 が既に使用されている

別のポートを使用：

```bash
uv run uvicorn web.main:app --reload --port 8001
```

## 本番環境デプロイ（将来）

### Docker を使用

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# uv をインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 依存関係をインストール
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# TailwindCSS をビルド
COPY web/static/css/input.css ./web/static/css/
COPY tailwind.config.js ./
RUN npx tailwindcss -i ./web/static/css/input.css \
                     -o ./web/static/css/output.css \
                     --minify

# アプリケーションをコピー
COPY . .

# データベースマイグレーション
RUN uv run alembic upgrade head

# Gunicorn + Uvicorn workers で起動
CMD ["uv", "run", "gunicorn", "web.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

```bash
# ビルド
docker build -t manganize-web .

# 実行
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your-key \
  -e DATABASE_URL=postgresql+asyncpg://... \
  manganize-web
```

## 次のステップ

- `/speckit.tasks` を実行してタスク一覧を生成
- `docs/specs/web-app/tasks.md` を参照して実装を開始
- 各 User Story (P1 → P2 → P3 → P4) の順に実装
