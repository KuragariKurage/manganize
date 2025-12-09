# カスタムツールを追加する

## ツールの基本構造

`@tool` デコレータで定義：

```python
from langchain.tools import tool

@tool
def my_tool(input: str) -> str:
    """ツールの説明。LLM がツール選択時に参照する。

    Args:
        input: 入力パラメータの説明

    Returns:
        処理結果の説明
    """
    return process(input)
```

## Researcher にツールを追加する

### ステップ 1: ツールを定義

`manganize/tools.py` に追加：

```python
@tool
def fetch_github_readme(repo: str) -> str:
    """GitHub リポジトリの README を取得する。

    Args:
        repo: owner/repo 形式のリポジトリ名

    Returns:
        README の内容
    """
    url = f"https://raw.githubusercontent.com/{repo}/main/README.md"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text
```

### ステップ 2: エージェントに登録

`manganize/agents.py` を編集：

```python
from manganize.tools import (
    generate_manga_image,
    read_document_file,
    retrieve_webpage,
    fetch_github_readme,  # 追加
)

class ManganizeAgent:
    def __init__(self, model: BaseChatModel | None = None):
        self.researcher = create_agent(
            model=...,
            tools=[
                retrieve_webpage,
                DuckDuckGoSearchRun(),
                read_document_file,
                fetch_github_readme,  # 追加
            ],
            ...
        )
```

## ツール実装のポイント

### 詳細なドキュメント

LLM がツールを適切に選択できるよう、docstring を詳細に記述：

```python
@tool
def search_papers(query: str, max_results: int = 5) -> str:
    """学術論文を検索する。技術的な背景情報が必要な場合に使用。

    Args:
        query: 検索クエリ（英語推奨）
        max_results: 取得する論文数（デフォルト: 5）

    Returns:
        論文のタイトルと要約のリスト
    """
```

### エラーハンドリング

```python
@tool
def risky_operation(input: str) -> str:
    """外部 API を呼び出す操作。"""
    try:
        return call_api(input)
    except requests.RequestException as e:
        return f"API 呼び出しに失敗: {e}"
```

### 型ヒント

```python
@tool
def typed_tool(
    text: str,
    max_length: int = 100,
    include_metadata: bool = False,
) -> str:
    """型ヒントの例。"""
    ...
```

## トラブルシューティング

### ツールが呼び出されない

- docstring が明確で詳細か確認
- ツール名が目的を示しているか確認
- パラメータの説明が具体的か確認

### 依存関係の追加

`pyproject.toml` に追加：

```toml
dependencies = [
    ...
    "new-package>=1.0.0",
]
```

```bash
uv sync
```
