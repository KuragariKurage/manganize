# 設定リファレンス

このドキュメントは、Manganize の設定ファイルとオプションを説明します。

## プロジェクト設定

### pyproject.toml

プロジェクトのメタデータと依存関係を定義します。

```toml
[project]
name = "manganize"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "google-genai>=1.52.0",
    "langchain>=1.1.0",
    "langchain-google-genai>=3.2.0",
    "langgraph>=1.0.4",
    "pillow>=12.0.0",
]

[dependency-groups]
dev = [
    "mypy>=1.19.0",
    "ruff>=0.14.7",
]
```

#### プロジェクトメタデータ

- `name`: パッケージ名
- `version`: バージョン番号（Semantic Versioning）
- `description`: プロジェクトの説明
- `readme`: README ファイルのパス
- `requires-python`: 必要な Python バージョン

#### 依存関係

- `dependencies`: 本番環境で必要なパッケージ
- `dependency-groups.dev`: 開発環境でのみ必要なパッケージ

#### 依存関係の追加

```bash
# 本番依存関係を追加
uv add package-name

# 開発依存関係を追加
uv add --dev package-name
```

### langgraph.json

LangGraph の設定ファイル。

```json
{
    "dependencies": [
        "."
    ],
    "graphs": {
        "manganize_agent": "main.py:agent"
    },
    "env": ".env"
}
```

#### フィールド

- `dependencies`: プロジェクトの依存関係（ローカルパッケージ）
- `graphs`: 定義されたエージェントグラフ
  - キー: グラフ名
  - 値: `ファイルパス:変数名` の形式
- `env`: 環境変数ファイルのパス

#### エージェントの追加

新しいエージェントを追加する場合：

```json
{
    "graphs": {
        "manganize_agent": "main.py:agent",
        "summarizer_agent": "summarizer.py:agent"
    }
}
```

### .env

環境変数を定義するファイル。

```bash
# Google Generative AI API キー
GOOGLE_API_KEY=your-api-key-here

# LangSmith トレーシング（オプション）
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=manganize

# その他の設定
MANGANIZE_OUTPUT_DIR=./output
MANGANIZE_LOG_LEVEL=INFO
```

#### 推奨される環境変数

| 変数名 | 説明 | 必須 | デフォルト |
|--------|------|------|----------|
| `GOOGLE_API_KEY` | Google Generative AI の API キー | ✓ | - |
| `LANGCHAIN_TRACING_V2` | LangSmith トレーシングの有効化 | - | `false` |
| `LANGCHAIN_API_KEY` | LangSmith の API キー | - | - |
| `LANGCHAIN_PROJECT` | LangSmith のプロジェクト名 | - | `default` |
| `MANGANIZE_OUTPUT_DIR` | 画像の出力ディレクトリ | - | `.` |
| `MANGANIZE_LOG_LEVEL` | ログレベル | - | `INFO` |

## ツール設定

### Taskfile.yml

タスクランナーの設定ファイル。

```yaml
# https://taskfile.dev

version: '3'

vars:
  GREETING: Hello, World!

tasks:
  default:
    cmds:
      - echo "{{.GREETING}}"
    silent: true

  lint:
    desc: コードをリント
    cmds:
      - uv run ruff check .

  format:
    desc: コードをフォーマット
    cmds:
      - uv run ruff format .

  typecheck:
    desc: 型チェック
    cmds:
      - uv run mypy manganize/

  run:
    desc: メインスクリプトを実行
    cmds:
      - uv run python main.py

  clean:
    desc: 生成ファイルをクリーンアップ
    cmds:
      - rm -rf __pycache__
      - rm -rf .mypy_cache
      - rm -rf .ruff_cache
      - rm -f generated_image.png
```

#### タスクの実行

```bash
# デフォルトタスク
task

# 特定のタスク
task lint
task format
task typecheck
task run
task clean
```

#### カスタムタスクの追加

```yaml
tasks:
  test:
    desc: テストを実行
    cmds:
      - uv run pytest tests/

  install:
    desc: 依存関係をインストール
    cmds:
      - uv sync
```

## Ruff 設定

### ruff.toml

Ruff のリント・フォーマット設定。プロジェクトルートに配置します。

```toml
# ruff.toml

[lint]
# 有効化するルール
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

# 無効化するルール
ignore = [
    "E501",  # line too long (フォーマッタが対応)
]

# ファイルごとのルール設定
[lint.per-file-ignores]
"__init__.py" = ["F401"]  # 未使用インポートを許可

[format]
# 行の最大長
line-length = 100

# インデント
indent-width = 4

# クォートスタイル
quote-style = "double"
```

#### 主要なルールカテゴリ

| カテゴリ | 説明 |
|---------|------|
| `E`, `W` | pycodestyle（PEP 8 準拠） |
| `F` | Pyflakes（未使用変数、インポートなど） |
| `I` | isort（インポートの並び順） |
| `B` | flake8-bugbear（バグの可能性） |
| `C4` | flake8-comprehensions（内包表記の最適化） |
| `UP` | pyupgrade（Python の新機能の推奨） |

### 実行方法

```bash
# リントチェック
uv run ruff check .

# 自動修正
uv run ruff check --fix .

# フォーマット
uv run ruff format .
```

## Mypy 設定

### mypy.ini または pyproject.toml

Mypy の型チェック設定。

```toml
# pyproject.toml に追加

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
strict_equality = true

# 外部ライブラリの型チェックをスキップ
[[tool.mypy.overrides]]
module = [
    "google.*",
    "langchain.*",
    "langgraph.*",
]
ignore_missing_imports = true
```

#### 主要なオプション

| オプション | 説明 | 推奨値 |
|-----------|------|--------|
| `python_version` | Python のバージョン | `"3.13"` |
| `disallow_untyped_defs` | 型ヒントのない関数を禁止 | `true` |
| `disallow_incomplete_defs` | 不完全な型ヒントを禁止 | `true` |
| `no_implicit_optional` | 暗黙の Optional を禁止 | `true` |
| `strict_equality` | 厳密な等価性チェック | `true` |
| `ignore_missing_imports` | 型情報のないモジュールを無視 | `true` |

### 実行方法

```bash
# 型チェック
uv run mypy manganize/

# 特定のファイルのみ
uv run mypy manganize/chain.py
```

## ログ設定

### Python の logging モジュール

```python
# logging_config.py

import logging
import os

def setup_logging():
    """ログ設定を初期化する。"""
    log_level = os.getenv("MANGANIZE_LOG_LEVEL", "INFO")

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("manganize.log"),
        ]
    )
```

```python
# main.py

from logging_config import setup_logging

setup_logging()

# ロガーを取得
logger = logging.getLogger(__name__)

logger.info("Starting Manganize")
```

### ログレベル

| レベル | 用途 |
|--------|------|
| `DEBUG` | 詳細なデバッグ情報 |
| `INFO` | 一般的な情報メッセージ |
| `WARNING` | 警告メッセージ |
| `ERROR` | エラーメッセージ |
| `CRITICAL` | 重大なエラー |

## デプロイ設定

### Dockerfile（オプション）

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# uv をインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 依存関係をコピー
COPY pyproject.toml uv.lock ./

# 依存関係をインストール
RUN uv sync --no-dev

# アプリケーションをコピー
COPY . .

# 環境変数
ENV GOOGLE_API_KEY=""

CMD ["uv", "run", "python", "main.py"]
```

### docker-compose.yml（オプション）

```yaml
version: '3.8'

services:
  manganize:
    build: .
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./output:/app/output
```

## まとめ

このリファレンスでは、以下の設定を説明しました。

- プロジェクト設定（pyproject.toml, langgraph.json）
- 環境変数（.env）
- ツール設定（Taskfile.yml）
- リント・フォーマット設定（ruff.toml）
- 型チェック設定（mypy.ini）
- ログ設定
- デプロイ設定（Dockerfile）

## 関連ドキュメント

- [API リファレンス](api.md) - API の詳細仕様
- [はじめての Manganize](../tutorials/getting-started.md) - セットアップ手順

