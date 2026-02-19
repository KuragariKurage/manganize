# 設定リファレンス

## pyproject.toml

```toml
[project]
name = "manganize"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "google-genai>=1.52.0",
    "langchain>=1.1.0",
    "langchain-community>=0.4.1",
    "langchain-google-genai>=3.2.0",
    "langgraph>=1.0.4",
    "markitdown[all]>=0.1.0",
    "pillow>=12.0.0",
    "playwright>=1.49.0",
]

[dependency-groups]
dev = [
    "ty>=0.0.1a6",
    "ruff>=0.14.7",
]
```

### 依存関係の追加

```bash
uv add package-name        # 本番依存
uv add --dev package-name  # 開発依存
```

## langgraph.json

```json
{
    "dependencies": ["."],
    "graphs": {
        "manganize_agent": "main.py:local_graph"
    },
    "env": ".env"
}
```

## 環境変数 (.env)

### コアエージェント設定

```bash
# 必須
GOOGLE_API_KEY=your-api-key

# オプション（LangSmith）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=manganize
```

| 変数 | 説明 | 必須 |
|------|------|------|
| `GOOGLE_API_KEY` | Google Generative AI API キー | ✓ |
| `LANGCHAIN_TRACING_V2` | LangSmith トレーシング | - |
| `LANGCHAIN_API_KEY` | LangSmith API キー | - |

### Web アプリ設定

`apps/web/manganize_web/config.py` で管理。

```bash
# データベース
DATABASE_URL=sqlite+aiosqlite:///./manganize.db

# アプリケーション
DEBUG=false
ENVIRONMENT=development

# レート制限
RATE_LIMIT_PER_MINUTE=10

# ファイルアップロード
MAX_FILE_SIZE_MB=10
UPLOAD_TTL_HOURS=24

# オブジェクトストレージ（S3互換: AWS S3 / Cloudflare R2 / MinIO）
STORAGE_PROVIDER=s3
STORAGE_BUCKET=manganize-uploads
STORAGE_REGION=ap-northeast-1
STORAGE_ENDPOINT_URL=           # MinIO / LocalStack など（デフォルト: None）
STORAGE_ACCESS_KEY_ID=          # オプション（None の場合は環境認証情報を使用）
STORAGE_SECRET_ACCESS_KEY=      # オプション
STORAGE_FORCE_PATH_STYLE=false
STORAGE_OBJECT_PREFIX=uploads
STORAGE_SIGNED_URL_TTL_SECONDS=900

# CORS
CORS_ORIGINS=["http://localhost:8000","http://127.0.0.1:8000"]
```

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `DATABASE_URL` | SQLAlchemy 接続文字列 | `sqlite+aiosqlite:///./manganize.db` |
| `DEBUG` | デバッグモード | `false` |
| `ENVIRONMENT` | 実行環境 (`development`/`production`) | `development` |
| `RATE_LIMIT_PER_MINUTE` | IP ごとのリクエスト上限/分 | `10` |
| `MAX_FILE_SIZE_MB` | アップロード上限 (MB) | `10` |
| `UPLOAD_TTL_HOURS` | アップロードデータの保持時間 | `24` |
| `STORAGE_PROVIDER` | ストレージプロバイダー (`s3`/`r2`/`minio`) | `s3` |
| `STORAGE_BUCKET` | バケット名 | `manganize-uploads` |
| `STORAGE_REGION` | リージョン | `ap-northeast-1` |
| `STORAGE_ENDPOINT_URL` | カスタムエンドポイント (LocalStack など) | `None` |
| `STORAGE_ACCESS_KEY_ID` | アクセスキー | `None` |
| `STORAGE_SECRET_ACCESS_KEY` | シークレットキー | `None` |
| `STORAGE_FORCE_PATH_STYLE` | パス形式 URL を強制 | `false` |
| `STORAGE_OBJECT_PREFIX` | オブジェクトキープレフィックス | `uploads` |
| `STORAGE_SIGNED_URL_TTL_SECONDS` | 署名付き URL の有効期限 (秒) | `900` |
| `CORS_ORIGINS` | 許可する CORS オリジンのリスト | `["http://localhost:8000","http://127.0.0.1:8000"]` |

## Taskfile.yml

```yaml
version: '3'

tasks:
  init:
    desc: setup local server
    deps: [docker:up]
    cmds:
      - uv run alembic upgrade head
      - uv run python scripts/seed_characters.py
      - npm install

  run:
    desc: Run the application (CLI agent)
    cmds:
      - uv run python main.py {{.CLI_ARGS}}

  lint:
    desc: Run the linter
    cmds:
      - uv run ruff check .

  format:
    desc: Run the formatter
    cmds:
      - uv run ruff check --fix .

  typecheck:
    desc: Run the type checker
    cmds:
      - uv run ty check .

  docker:up:
    desc: Start Docker services (LocalStack S3)
    cmds:
      - docker compose up -d

  docker:down:
    desc: Stop Docker services
    cmds:
      - docker compose down

  docker:logs:
    desc: Show Docker service logs
    cmds:
      - docker compose logs -f {{.CLI_ARGS}}

  dev:fastapi:
    desc: Run the fastapi development server
    deps: [docker:up]
    cmds:
      - uv run fastapi dev apps/web/manganize_web/main.py --reload-dir apps/web --reload-dir packages/core

  dev:tailwindcss:
    desc: Run the tailwindcss development server
    cmds:
      - npx @tailwindcss/cli -i apps/web/manganize_web/static/css/input.css -o apps/web/manganize_web/static/css/output.css --watch

  build:tailwindcss:
    desc: Build the tailwindcss output for production
    cmds:
      - npx @tailwindcss/cli -i apps/web/manganize_web/static/css/input.css -o apps/web/manganize_web/static/css/output.css --minify

  dev:
    desc: Run the web application in development mode with hot reload
    deps: [dev:fastapi, dev:tailwindcss]

  web:
    desc: Alias for dev task
    cmds:
      - task: dev
```

実行:

```bash
task lint           # Ruff リント
task format         # Ruff フォーマット（ruff check --fix）
task typecheck      # ty 型チェック
task run -- "URL またはテキスト"
task docker:up      # Docker サービス起動（LocalStack）
task docker:down    # Docker サービス停止
task docker:logs    # Docker ログ確認
task dev            # 開発サーバー起動（FastAPI + TailwindCSS）
task dev:fastapi    # FastAPI のみ起動
task dev:tailwindcss # TailwindCSS watch モード
task build:tailwindcss # TailwindCSS 本番ビルド
task web            # dev のエイリアス
```

## Ruff 設定

`pyproject.toml` に追加:

```toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.ruff.format]
line-length = 100
quote-style = "double"
```

## ty 設定

型チェッカーとして ty を使用:

```bash
uv run ty check .
```
