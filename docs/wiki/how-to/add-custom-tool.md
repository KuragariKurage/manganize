# カスタムツールを追加する

このガイドでは、Manganize エージェントに独自のツールを追加する方法を説明します。

## 目的

- LangChain ツールの基本を理解する
- Manganize に新しい機能を追加する
- ツールの実装パターンを学ぶ

## ツールの基本構造

LangChain のツールは、`@tool` デコレータを使って定義します。

```python
from langchain.tools import tool

@tool
def my_custom_tool(input: str) -> str:
    """ツールの説明をここに記述します。

    この説明は、LLM がツールを選択する際に参照されます。

    Args:
        input: 入力パラメータの説明

    Returns:
        処理結果の説明
    """
    # ツールの実装
    result = process(input)
    return result
```

## 例 1: テキスト要約ツールを追加する

### ステップ 1: ツールを定義する

`manganize/tools.py` に新しいツールを追加します。

```python
from langchain.tools import tool
from langgraph.types import Command

@tool
def summarize_text(text: str, max_points: int = 5, runtime: ToolRuntime) -> Command:
    """長いテキストを要約するツール。

    テキストコンテンツが長すぎる場合に、主要なポイントを抽出して
    要約します。要約されたテキストは、漫画生成に適した長さになります。

    Args:
        text: 要約したいテキスト
        max_points: 抽出する主要ポイントの最大数（デフォルト: 5）

    Returns:
        Command: 要約されたテキストを含むコマンド
    """
    from langchain.chat_models import init_chat_model

    # LLM を使ってテキストを要約
    model = init_chat_model(model="google_genai:gemini-2.5-flash")

    prompt = f"""
    以下のテキストを、最大{max_points}つの主要ポイントに要約してください。
    各ポイントは、漫画の1コマで表現できる程度の長さにしてください。

    テキスト:
    {text}

    要約:
    """

    response = model.invoke(prompt)
    summarized_text = response.content

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"テキストを要約しました:\n{summarized_text}",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )
```

### ステップ 2: ツールをエージェントに登録する

`manganize/chain.py` を編集して、ツールを追加します。

```python
from manganize.tools import generate_manga_image, summarize_text

class ManganizeAgent:
    def __init__(self, model: BaseChatModel | None = None):
        self.agent = create_agent(
            model=model or init_chat_model(model="google_genai:gemini-2.5-flash"),
            tools=[generate_manga_image, summarize_text],  # ツールを追加
            state_schema=ManganizeAgentState,
            system_prompt=SystemMessage(
                content="You are a helpful assistant. Be concise and accurate."
            ),
            checkpointer=InMemorySaver(),
        )
```

### ステップ 3: ツールを使用する

エージェントは自動的に適切なタイミングでツールを使用します。

```python
agent = ManganizeAgent()

result = agent(
    "この長い小説を漫画にしてください: " + long_novel_text,
    thread_id="1",
)
```

エージェントは、テキストが長いと判断した場合、自動的に `summarize_text` ツールを呼び出します。

## 例 2: 画像保存ツールを追加する

### ステップ 1: ツールを定義する

```python
from pathlib import Path
from datetime import datetime

@tool
def save_manga_image(output_path: str | None = None, runtime: ToolRuntime) -> Command:
    """生成された漫画画像をファイルに保存するツール。

    Args:
        output_path: 保存先のパス（省略時は自動生成）

    Returns:
        Command: 保存結果を含むコマンド
    """
    from PIL import Image
    from io import BytesIO

    # 現在の状態から画像データを取得
    state = runtime.state
    image_data = state.get("generated_image")

    if not image_data:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content="保存する画像がありません。先に画像を生成してください。",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )

    # 出力パスを決定
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"manga_{timestamp}.png"

    # 画像を保存
    image = Image.open(BytesIO(image_data))
    image.save(output_path)

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"画像を保存しました: {output_path}",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )
```

### ステップ 2: 状態に依存するツール

このツールは、エージェントの状態（`generated_image`）に依存します。`runtime.state` を使って状態にアクセスできます。

## 例 3: 外部 API を呼び出すツール

### Wikipedia 検索ツール

漫画のコンテンツに関連する情報を Wikipedia から取得するツールを作成します。

```python
import requests

@tool
def search_wikipedia(query: str, lang: str = "ja", runtime: ToolRuntime) -> Command:
    """Wikipedia で情報を検索するツール。

    漫画のコンテンツに関連する背景情報や詳細を取得します。

    Args:
        query: 検索クエリ
        lang: 言語コード（デフォルト: "ja"）

    Returns:
        Command: 検索結果を含むコマンド
    """
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{query}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        summary = data.get("extract", "情報が見つかりませんでした。")

        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"Wikipedia の情報:\n{summary}",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )
    except Exception as e:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"検索に失敗しました: {str(e)}",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )
```

### 依存関係を追加する

`pyproject.toml` に `requests` を追加します。

```toml
[project]
dependencies = [
    ...
    "requests>=2.32.0",
]
```

```bash
uv sync
```

## ツール実装のベストプラクティス

### 1. 詳細なドキュメント文字列を書く

```python
@tool
def my_tool(param: str) -> str:
    """ツールの簡潔な説明。

    より詳細な説明をここに記述します。LLM はこの説明を読んで、
    ツールをいつ使用すべきか判断します。

    Args:
        param: パラメータの詳細な説明

    Returns:
        戻り値の詳細な説明

    Example:
        >>> result = my_tool("example")
        >>> print(result)
        "processed: example"
    """
    pass
```

### 2. 適切なエラーハンドリング

```python
@tool
def robust_tool(input: str, runtime: ToolRuntime) -> Command:
    """堅牢なツールの例。"""
    try:
        result = risky_operation(input)
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"成功: {result}",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )
    except ValueError as e:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"入力が不正です: {str(e)}",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )
    except Exception as e:
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=f"エラーが発生しました: {str(e)}",
                        tool_call_id=runtime.tool_call_id,
                    )
                ]
            }
        )
```

### 3. 型ヒントを必ず付ける

```python
from typing import Optional

@tool
def typed_tool(
    text: str,
    max_length: int = 100,
    include_metadata: bool = False,
    runtime: ToolRuntime,
) -> Command:
    """型ヒントの例。"""
    pass
```

### 4. テストを書く

```python
# tests/test_tools.py

def test_summarize_text():
    from manganize.tools import summarize_text

    long_text = "..." * 1000
    result = summarize_text.invoke({"text": long_text, "max_points": 3})

    assert result is not None
    assert len(result.update["messages"]) > 0
```

## トラブルシューティング

### ツールが呼び出されない

LLM がツールを選択するために、以下を確認してください。

- ドキュメント文字列が明確で詳細であること
- ツール名が目的を示していること
- パラメータの説明が具体的であること

### ツールの実行が失敗する

- エラーハンドリングが適切に実装されているか
- 必要な依存関係がインストールされているか
- API キーや認証情報が正しく設定されているか

## まとめ

このガイドでは、以下を学びました。

- LangChain ツールの基本構造
- Manganize にカスタムツールを追加する方法
- 外部 API を呼び出すツールの実装
- ツール実装のベストプラクティス

## 関連ドキュメント

- [API リファレンス - Tools](../reference/api.md#tools) - ツール API の詳細
- [LangGraph を理解する](../tutorials/understanding-langgraph.md) - エージェントとツールの関係
- [アーキテクチャの理解](../explanation/architecture.md) - ツールがどのように統合されるか

