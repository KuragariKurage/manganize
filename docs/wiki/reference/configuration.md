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
    "pyrefly>=0.44.1",
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

## Taskfile.yml

```yaml
version: '3'

tasks:
  lint:
    cmds:
      - uv run ruff check .

  format:
    cmds:
      - uv run ruff format .

  typecheck:
    cmds:
      - uv run pyrefly check manganize/

  run:
    cmds:
      - uv run python main.py {{.CLI_ARGS}}
```

実行:

```bash
task lint
task format
task typecheck
task run -- "URL またはテキスト"
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

## Pyrefly 設定

型チェッカーとして Pyrefly を使用:

```bash
uv run pyrefly check manganize/
```
