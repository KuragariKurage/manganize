# LangGraph を理解する

このチュートリアルでは、Manganize で使用されている LangGraph の基本概念を学びます。

## 対象読者

- LangChain の基本を理解している方
- エージェントシステムの構造を学びたい方

## 所要時間

約 20 分

## LangGraph とは

LangGraph は、LangChain 上に構築されたエージェントフレームワークで、以下の特徴があります：

- **状態管理**: エージェントの状態を明示的に管理
- **グラフベース**: 処理フローをグラフ構造で表現
- **チェックポイント**: 会話履歴や状態を保存・復元

## Manganize における LangGraph の使い方

### ステップ 1: エージェントの状態を理解する

Manganize では、`ManganizeAgentState` でエージェントの状態を定義しています。

```python
class ManganizeAgentState(AgentState):
    generated_image: Optional[bytes]
```

この状態には、生成された画像データが格納されます。

### ステップ 2: エージェントの作成

`ManganizeAgent` クラスでは、`create_agent` 関数を使ってエージェントを作成します。

```python
self.agent = create_agent(
    model=model or init_chat_model(model="google_genai:gemini-2.5-flash"),
    tools=[generate_manga_image],  # 使用するツール
    state_schema=ManganizeAgentState,  # 状態のスキーマ
    system_prompt=SystemMessage(...),  # システムプロンプト
    checkpointer=InMemorySaver(),  # 状態を保存するチェックポインター
)
```

### ステップ 3: エージェントの実行

エージェントは `invoke` メソッドで実行されます。

```python
config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
messages = {"messages": input_text}
response = self.agent.invoke(messages, config)
```

`thread_id` は会話セッションを識別するための ID で、同じ `thread_id` を使うことで会話履歴を維持できます。

## ツールの仕組み

### ステップ 4: ツールの定義

Manganize では、`generate_manga_image` ツールを定義しています。

```python
@tool
def generate_manga_image(content: str, runtime: ToolRuntime) -> Command:
    """漫画風の画像を生成するツール。"""
    # Gemini API を呼び出して画像を生成
    ...

    # 結果を Command として返す
    return Command(
        update={
            "generated_image": image_data,
            "messages": [ToolMessage(...)]
        }
    )
```

`@tool` デコレータを使うことで、LangChain のツールとして認識されます。

### ステップ 5: Command による状態更新

`Command` オブジェクトは、エージェントの状態を更新するために使用されます。

```python
return Command(
    update={
        "generated_image": image_data,  # 状態に画像データを追加
        "messages": [ToolMessage(...)]  # メッセージ履歴に追加
    }
)
```

## 実践: 独自のツールを追加する

新しいツールを追加してみましょう。例えば、生成された画像を Twitter に投稿するツールを作成します。

```python
from langchain.tools import tool
from langgraph.types import Command

@tool
def post_to_twitter(image_data: bytes, runtime: ToolRuntime) -> Command:
    """生成された画像を Twitter に投稿するツール。"""
    # Twitter API を使って投稿（実装は省略）
    success = upload_to_twitter(image_data)

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content="Twitter に投稿しました" if success else "投稿に失敗しました",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )
```

このツールを `ManganizeAgent` に追加するには、`chain.py` を編集します。

```python
from manganize.tools import generate_manga_image, post_to_twitter

class ManganizeAgent:
    def __init__(self, model: BaseChatModel | None = None):
        self.agent = create_agent(
            model=model or init_chat_model(model="google_genai:gemini-2.5-flash"),
            tools=[generate_manga_image, post_to_twitter],  # ツールを追加
            ...
        )
```

## チェックポイントの活用

### ステップ 6: 会話履歴の維持

`InMemorySaver` を使うことで、会話履歴がメモリに保存されます。

```python
# 最初の会話
result1 = agent("猫のストーリーを漫画にして", thread_id="cat-story")

# 同じ thread_id で続きを実行
result2 = agent("もっとかわいくして", thread_id="cat-story")
```

同じ `thread_id` を使うことで、エージェントは以前の会話を参照して応答します。

## まとめ

このチュートリアルでは、以下を学びました：

- LangGraph の基本概念
- Manganize におけるエージェントの構造
- ツールの定義と状態更新
- チェックポイントによる会話履歴の管理

## 次のステップ

- [アーキテクチャの理解](../explanation/architecture.md) - システム全体の設計を理解する
- [カスタムツールの追加方法](../how-to/add-custom-tool.md) - 独自のツールを実装する
- [API リファレンス](../reference/api.md) - 詳細な API 仕様を確認する

