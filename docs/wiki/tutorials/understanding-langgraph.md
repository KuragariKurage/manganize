# LangGraph を理解する

## LangGraph とは

LangChain 上に構築されたエージェントフレームワーク。

- **状態管理**: エージェントの状態を明示的に管理
- **グラフベース**: 処理フローをノードとエッジで表現
- **チェックポイント**: 会話履歴や状態を保存・復元

## Manganize のグラフ構造

```
START → Researcher → Scenario Writer → Image Generator → END
```

### 状態スキーマ

```python
class ManganizeInput(TypedDict):
    topic: str

class ManganizeState(TypedDict):
    research_results: str
    scenario: str

class ManganizeOutput(TypedDict):
    generated_image: Optional[bytes]

class ManganizeAgentState(ManganizeInput, ManganizeState, ManganizeOutput):
    pass
```

### グラフの構築

```python
def compile_graph(self) -> StateGraph:
    builder = StateGraph(
        state_schema=ManganizeAgentState,
        input_schema=ManganizeInput,
        output_schema=ManganizeOutput,
    )

    # ノードを追加
    builder.add_node("researcher", self._researcher_node)
    builder.add_node("scenario_writer", self._scenario_writer_node)
    builder.add_node("image_generator", self._image_generator_node)

    # エッジを追加
    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "scenario_writer")
    builder.add_edge("scenario_writer", "image_generator")

    return builder.compile(checkpointer=InMemorySaver())
```

## ノードの実装

各ノードは `Command` を返して次のノードへ遷移：

```python
def _researcher_node(self, state: ManganizeAgentState) -> Command:
    result = self.researcher.invoke(
        {"messages": [{"role": "user", "content": state["topic"]}]}
    )
    return Command(
        update={"research_results": result["messages"][-1].content},
        goto="scenario_writer",
    )
```

## チェックポイント

`InMemorySaver` で会話履歴を保持：

```python
config = {"configurable": {"thread_id": "1"}}

# 同じ thread_id で実行すると履歴を参照
result1 = graph.invoke({"topic": "Kubernetes"}, config)
result2 = graph.invoke({"topic": "続きを詳しく"}, config)
```

## エージェントの作成

`create_agent` でツール付きエージェントを作成：

```python
self.researcher = create_agent(
    model=init_chat_model(model="google_genai:gemini-3-pro-preview"),
    tools=[retrieve_webpage, DuckDuckGoSearchRun(), read_document_file],
    system_prompt=SystemMessage(content=MANGANIZE_RESEARCHER_SYSTEM_PROMPT),
)
```

## 次のステップ

- [アーキテクチャ解説](../explanation/architecture.md) - システム全体の設計
- [カスタムツールの追加](../how-to/add-custom-tool.md) - ツールの実装方法
