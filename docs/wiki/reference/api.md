# API リファレンス

## ManganizeAgent

### クラス定義

```python
from manganize.agents import ManganizeAgent

class ManganizeAgent:
    def __init__(self, model: BaseChatModel | None = None): ...
    def compile_graph(self) -> StateGraph: ...
```

### コンストラクタ

```python
ManganizeAgent(model=None)
```

- `model`: 使用する LLM。`None` の場合は `google_genai:gemini-3-pro-preview`

### compile_graph()

LangGraph のグラフをコンパイルして返す。

```python
agent = ManganizeAgent()
graph = agent.compile_graph()

config = {"configurable": {"thread_id": "1"}}
result = graph.invoke({"topic": "テーマ"}, config)
```

## 状態スキーマ

### 入力 (ManganizeInput)

```python
class ManganizeInput(TypedDict):
    topic: str  # 漫画化したいテーマ（URL またはテキスト）
```

### 出力 (ManganizeOutput)

```python
class ManganizeOutput(TypedDict):
    generated_image: Optional[bytes]  # PNG 画像データ
```

### 中間状態 (ManganizeState)

```python
class ManganizeState(TypedDict):
    research_results: str  # Researcher の出力
    scenario: str          # Scenario Writer の出力
```

## ツール

### generate_manga_image

```python
def generate_manga_image(content: str) -> bytes | None
```

脚本から漫画画像を生成する。

- **content**: 漫画の脚本
- **戻り値**: PNG 画像データ、失敗時は `None`
- **モデル**: `gemini-3-pro-image-preview`
- **アスペクト比**: 9:16
- **解像度**: 2K

### retrieve_webpage

```python
@tool
def retrieve_webpage(url: str) -> str
```

Web ページを取得して Markdown に変換する。Playwright で JS レンダリング後の HTML を取得。

### read_document_file

```python
@tool
def read_document_file(source: str) -> str
```

ドキュメントファイルを読み取って Markdown に変換する。

対応形式: PDF, Word, PowerPoint, Excel, テキスト, 画像（OCR）

## プロンプト

### MANGANIZE_RESEARCHER_SYSTEM_PROMPT

Researcher エージェント用。技術情報を構造化されたファクトシートに整理する。

### MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT

Scenario Writer エージェント用。ファクトシートから 4 コマ漫画の脚本を作成する。

### MANGANIZE_IMAGE_GENERATION_SYSTEM_PROMPT

Image Generator 用。「まんがタイムきらら」風の画像生成指示。

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `GOOGLE_API_KEY` | Google Generative AI API キー（必須） |
| `LANGCHAIN_TRACING_V2` | LangSmith トレーシング有効化 |
| `LANGCHAIN_API_KEY` | LangSmith API キー |
