# LangGraph を理解する

Manganize の AI エージェントは LangGraph で実装されています。このチュートリアルでは、その仕組みを解説します。

## LangGraph とは

LangChain 上に構築されたエージェントフレームワーク。

- **状態管理**: エージェントの状態を明示的に管理
- **グラフベース**: 処理フローをノードとエッジで表現
- **チェックポイント**: 会話履歴や状態を保存・復元

## Manganize のグラフ構造

```
START → Researcher → [関連度チェック] → Scenario Writer → Image Generator → END
                          ↓
                     関連度 < 0.5
                          ↓
                         END（中断）
```

Researcher の後に**関連度チェック**（conditional edge）があり、トピックとの関連度が閾値未満の場合はパイプラインを中断します。

### ノード名の定義

```python
class NodeName(StrEnum):
    RESEARCHER = "researcher"
    SCENARIO_WRITER = "scenario_writer"
    IMAGE_GENERATOR = "image_generator"
```

### 状態スキーマ

```python
class ManganizeInput(TypedDict):
    topic: str                           # ユーザ入力（テキスト / URL / ファイルパス）

class ManganizeState(TypedDict):
    research_results: str                # リサーチで収集されたファクトシート
    research_results_relevance: float    # トピックとの関連度（0.0〜1.0）
    scenario: str                        # 4 コマ漫画のシナリオ

class ManganizeOutput(TypedDict):
    topic_title: str                     # 自動抽出されたタイトル
    generated_image: Optional[bytes]     # 最終的なマンガ画像（PNG）

class ManganizeAgentState(ManganizeInput, ManganizeState, ManganizeOutput):
    pass
```

### グラフの構築

```python
def compile_graph(
    self, checkpointer: BaseCheckpointSaver | None = None
) -> CompiledStateGraph:
    if checkpointer is None:
        checkpointer = InMemorySaver()

    builder = StateGraph(
        state_schema=ManganizeAgentState,
        input_schema=ManganizeInput,
        output_schema=ManganizeOutput,
    )

    # ノードを追加
    builder.add_node(NodeName.RESEARCHER, self._researcher_node)
    builder.add_node(NodeName.SCENARIO_WRITER, self._scenario_writer_node)
    builder.add_node(NodeName.IMAGE_GENERATOR, self._image_generator_node)

    # エッジを追加
    builder.add_edge(START, NodeName.RESEARCHER)
    builder.add_conditional_edges(
        NodeName.RESEARCHER,
        self._check_relevance,
        path_map={
            "researcher_is_not_relevant": END,
            "researcher_is_relevant": NodeName.SCENARIO_WRITER,
        },
    )
    builder.add_edge(NodeName.SCENARIO_WRITER, NodeName.IMAGE_GENERATOR)

    return builder.compile(checkpointer=checkpointer)
```

## ノードの実装

### Researcher ノード

DuckDuckGo 検索、Web スクレイピング（Playwright）、ドキュメント読み込み（MarkItDown）のツールを持つエージェント。構造化出力 `ResearcherAgentOutput` を返します。

```python
class ResearcherAgentOutput(BaseModel):
    topic_title: str = Field(description="トピックのタイトル")
    output: str = Field(description="構造化されたネタ帳（ファクトシート）の出力内容")
    relevance: float = Field(
        description="ユーザの入力に対する出力内容の関連度（0.0から1.0の間）"
    )

def _researcher_node(self, state: ManganizeAgentState) -> Command:
    result = self.researcher.invoke(
        {"messages": [{"role": "user", "content": state["topic"] + self.today_prompt}]}
    )
    response = result["structured_response"]
    return Command(
        update={
            "topic_title": response.topic_title,
            "research_results": response.output,
            "research_results_relevance": response.relevance,
        },
    )
```

### 関連度チェック（Conditional Edge）

Researcher の出力に含まれる `relevance` スコアが閾値（デフォルト 0.5）未満の場合、パイプラインを中断して無関係なコンテンツの生成を防ぎます。

```python
def _check_relevance(
    self, state: ManganizeAgentState
) -> Literal["researcher_is_not_relevant", "researcher_is_relevant"]:
    if state["research_results_relevance"] < self.relevance_threshold:
        return "researcher_is_not_relevant"
    return "researcher_is_relevant"
```

### Scenario Writer ノード

リサーチ結果をもとに 4 コマ漫画のシナリオを生成：

```python
def _scenario_writer_node(self, state: ManganizeAgentState) -> Command:
    result = self.scenario_writer.invoke(
        {"messages": [{"role": "user", "content": state["research_results"] + self.today_prompt}]}
    )
    last_message = result["messages"][-1]
    content = (
        last_message.content
        if isinstance(last_message.content, str)
        else str(last_message.content)
    )
    return Command(
        update={"scenario": content},
        goto=NodeName.IMAGE_GENERATOR,
    )
```

### Image Generator ノード

シナリオとキャラクター設定をもとに Gemini でマンガ画像を生成：

```python
def _image_generator_node(self, state: ManganizeAgentState) -> Command:
    result = generate_manga_image(state["scenario"], self.character)
    return Command(update={"generated_image": result}, goto=END)
```

## エージェントの初期化

`ManganizeAgent` はキャラクター、LLM、関連度閾値を受け取って初期化されます：

```python
agent = ManganizeAgent(
    character=KurageChan(),                                          # キャラクター
    researcher_llm=init_chat_model("google_genai:gemini-2.5-pro"),   # リサーチ用 LLM
    scenario_writer_llm=init_chat_model("google_genai:gemini-2.5-flash"),  # シナリオ用 LLM
    relevance_threshold=0.5,                                         # 関連度閾値
)
```

各エージェントの作成：

```python
# Researcher: ツール付き + 構造化出力
self.researcher = create_agent(
    model=researcher_llm or init_chat_model(model="google_genai:gemini-2.5-pro"),
    tools=[retrieve_webpage, DuckDuckGoSearchRun(), read_document_file],
    system_prompt=SystemMessage(content=get_researcher_system_prompt()),
    response_format=ResearcherAgentOutput,
)

# Scenario Writer: テキスト生成のみ（キャラクター設定をプロンプトに反映）
self.scenario_writer = create_agent(
    model=scenario_writer_llm or init_chat_model(model="google_genai:gemini-2.5-flash"),
    system_prompt=SystemMessage(
        content=get_scenario_writer_system_prompt(self.character)
    ),
)
```

## チェックポイント

デフォルトでは `InMemorySaver` を使用しますが、`compile_graph()` にカスタムの `checkpointer` を渡すことも可能です：

```python
config = {"configurable": {"thread_id": "1"}}

# 同じ thread_id で実行すると履歴を参照
result1 = graph.invoke({"topic": "Kubernetes"}, config)
result2 = graph.invoke({"topic": "続きを詳しく"}, config)
```

## 次のステップ

- [アーキテクチャ解説](../explanation/architecture.md) - システム全体の設計
- [カスタムツールの追加](../how-to/add-custom-tool.md) - ツールの実装方法
- [Reference: API Endpoints](../reference/api-endpoints.md) - Web API 仕様
