# API リファレンス

このドキュメントは、Manganize の API 仕様を網羅的に説明します。

## ManganizeAgent

### クラス定義

```python
class ManganizeAgent:
    def __init__(self, model: BaseChatModel | None = None):
        ...

    def __call__(self, input_text: str, thread_id: str) -> dict[str, Any]:
        ...
```

### `__init__(model: BaseChatModel | None = None)`

ManganizeAgent のインスタンスを初期化します。

**パラメータ:**

- `model` (BaseChatModel | None): 使用する言語モデル。`None` の場合は `google_genai:gemini-2.5-flash` がデフォルトで使用されます。

**例:**

```python
from langchain.chat_models import init_chat_model
from manganize.chain import ManganizeAgent

# デフォルトモデルを使用
agent = ManganizeAgent()

# カスタムモデルを使用
custom_model = init_chat_model(model="google_genai:gemini-1.5-pro")
agent = ManganizeAgent(model=custom_model)
```

### `__call__(input_text: str, thread_id: str) -> dict[str, Any]`

エージェントを実行して、テキストを漫画に変換します。

**パラメータ:**

- `input_text` (str): 漫画化したいテキストコンテンツ。
- `thread_id` (str): 会話セッションを識別するための ID。同じ `thread_id` を使うことで会話履歴を維持できます。

**戻り値:**

- `dict[str, Any]`: エージェントの実行結果。以下のキーを含みます。
  - `"messages"`: エージェントとのメッセージ履歴（list）
  - `"generated_image"`: 生成された画像データ（bytes | None）

**例:**

```python
agent = ManganizeAgent()

result = agent(
    input_text="猫が魚を見つけて喜ぶストーリー",
    thread_id="story-001",
)

# 画像データを取得
if result.get("generated_image"):
    image_data = result["generated_image"]
    # 画像を保存
    from PIL import Image
    from io import BytesIO
    image = Image.open(BytesIO(image_data))
    image.save("manga.png")
```

## ManganizeAgentState

### クラス定義

```python
class ManganizeAgentState(AgentState):
    generated_image: Optional[bytes]
```

エージェントの状態を表すクラス。

**属性:**

- `generated_image` (Optional[bytes]): 生成された画像データ。PNG 形式のバイト列。

## Tools

### generate_manga_image

```python
@tool
def generate_manga_image(content: str, runtime: ToolRuntime) -> Command:
    """漫画風の画像を生成するツール。"""
    ...
```

漫画風の画像を生成するツール。

**パラメータ:**

- `content` (str): 画像生成のためのコンテンツ。漫画化したいテキストやストーリーの説明を含む。
- `runtime` (ToolRuntime): LangChain のツールランタイム。自動的に渡されます。

**戻り値:**

- `Command`: LangGraph の Command オブジェクト。
  - 成功時: `update={"generated_image": bytes, "messages": [ToolMessage]}` で画像データを含む
  - 失敗時: `update={"generated_image": None, "messages": [ToolMessage]}` でエラーメッセージを含む

**画像仕様:**

- **モデル**: `gemini-3-pro-image-preview`
- **アスペクト比**: `9:16` (1152×2048px)
- **画像サイズ**: `2K`
- **形式**: PNG
- **ツール**: Google Search が有効

**例:**

エージェントが自動的に呼び出します。手動で呼び出す場合：

```python
from manganize.tools import generate_manga_image

result = generate_manga_image.invoke({
    "content": "可愛い女の子が笑顔で挨拶している"
})

if result.update.get("generated_image"):
    image_data = result.update["generated_image"]
```

## Prompts

### MANGANIZE_AGENT_SYSTEM_PROMPT

```python
MANGANIZE_AGENT_SYSTEM_PROMPT: str
```

漫画生成用のシステムプロンプト。

**構造:**

```
# Role
作家の役割定義

# Character Reference
キャラクターの外見と性格

# Art Style & Layout
アートスタイルと構成

# Negative Constraints
禁止事項

# Content / Story
{content} ← ここにコンテンツが挿入される
```

**使用方法:**

```python
from manganize.prompts import MANGANIZE_AGENT_SYSTEM_PROMPT

# content を埋め込む
prompt = MANGANIZE_AGENT_SYSTEM_PROMPT.format(
    content="猫が魚を見つけるストーリー"
)
```

**カスタマイズ:**

`manganize/prompts.py` を編集してプロンプトをカスタマイズできます。

## 型定義

### BaseChatModel

LangChain の言語モデルの基底クラス。

```python
from langchain.chat_models import BaseChatModel, init_chat_model

model = init_chat_model(model="google_genai:gemini-2.5-flash")
```

### Command

LangGraph の Command オブジェクト。ツールの実行結果を表します。

```python
from langgraph.types import Command

command = Command(
    update={
        "key": "value",
        "messages": [ToolMessage(content="result", tool_call_id="id")]
    }
)
```

### ToolRuntime

LangChain のツールランタイム。ツールの実行コンテキストを提供します。

**属性:**

- `tool_call_id` (str): ツール呼び出しの ID
- `state` (dict): エージェントの現在の状態

```python
@tool
def my_tool(input: str, runtime: ToolRuntime) -> Command:
    tool_call_id = runtime.tool_call_id
    current_state = runtime.state
    ...
```

## ImageConfig

Gemini API の画像生成設定。

```python
from google.genai import types

config = types.ImageConfig(
    aspect_ratio="9:16",
    image_size="2K"
)
```

### aspect_ratio

画像のアスペクト比。

**利用可能な値:**

| 値 | 説明 | 解像度（2K の場合） |
|----|------|-------------------|
| `"1:1"` | 正方形 | 2048×2048 |
| `"3:4"` | 縦長 | 1536×2048 |
| `"4:3"` | 横長 | 2048×1536 |
| `"9:16"` | 縦長（スマホ向け） | 1152×2048 |
| `"16:9"` | 横長（PC/TV 向け） | 2048×1152 |

### image_size

画像のサイズ。

**利用可能な値:**

- `"1K"`: 低解像度（約 1024px）
- `"2K"`: 標準解像度（約 2048px）
- `"4K"`: 高解像度（約 4096px）

## GenerateContentConfig

Gemini API のコンテンツ生成設定。

```python
from google.genai import types

config = types.GenerateContentConfig(
    image_config=types.ImageConfig(
        aspect_ratio="9:16",
        image_size="2K"
    ),
    tools=[{"google_search": {}}],  # Google Search を有効化
    temperature=0.7,                # 生成の多様性（0.0 - 1.0）
    top_p=0.95,                     # Nucleus sampling
    top_k=40,                       # Top-K sampling
)
```

### パラメータ

- `image_config` (ImageConfig): 画像生成設定
- `tools` (list): 使用する外部ツール（例: Google Search）
- `temperature` (float): 生成の多様性（デフォルト: 1.0）
  - 低い値（0.0-0.3）: 決定論的、一貫性のある出力
  - 中程度（0.4-0.7）: バランスの取れた出力
  - 高い値（0.8-1.0）: 創造的、多様な出力
- `top_p` (float): Nucleus sampling のパラメータ（デフォルト: 0.95）
- `top_k` (int): Top-K sampling のパラメータ（デフォルト: 40）

## エラーハンドリング

### 一般的なエラー

#### APIKeyError

Google Generative AI の API キーが設定されていない場合に発生します。

**解決方法:**

```bash
export GOOGLE_API_KEY="your-api-key"
```

または `.env` ファイルに記述します。

#### ImageGenerationError

画像生成が失敗した場合に発生します。

**原因:**

- API の利用制限に達した
- ネットワークエラー
- 不適切なコンテンツ

**確認方法:**

```python
result = agent("コンテンツ", thread_id="1")

if result.get("generated_image") is None:
    # 画像生成が失敗
    messages = result.get("messages", [])
    for msg in messages:
        if isinstance(msg, ToolMessage):
            print(f"エラー: {msg.content}")
```

## 環境変数

### GOOGLE_API_KEY

Google Generative AI の API キー。

```bash
export GOOGLE_API_KEY="your-api-key"
```

### その他の環境変数

LangChain や LangGraph の動作に影響する環境変数：

- `LANGCHAIN_TRACING_V2`: LangSmith トレーシングを有効化（`true` / `false`）
- `LANGCHAIN_API_KEY`: LangSmith の API キー
- `LANGCHAIN_PROJECT`: LangSmith のプロジェクト名

## 例

### 基本的な使用例

```python
from manganize.chain import ManganizeAgent
from PIL import Image
from io import BytesIO

agent = ManganizeAgent()

result = agent(
    "猫が魚を見つけて喜ぶストーリー",
    thread_id="story-001",
)

if result.get("generated_image"):
    image = Image.open(BytesIO(result["generated_image"]))
    image.save("manga.png")
```

### 会話を続ける例

```python
agent = ManganizeAgent()

# 最初のリクエスト
result1 = agent(
    "猫が魚を見つけるストーリーを漫画にして",
    thread_id="cat-story",
)

# 同じ thread_id で続きをリクエスト
result2 = agent(
    "もっとかわいくして",
    thread_id="cat-story",
)
```

### カスタムモデルを使用する例

```python
from langchain.chat_models import init_chat_model
from manganize.chain import ManganizeAgent

# より高性能なモデルを使用
model = init_chat_model(
    model="google_genai:gemini-1.5-pro",
    temperature=0.8,
)

agent = ManganizeAgent(model=model)
```

## バージョン情報

- **Manganize**: 0.1.0
- **Python**: 3.13+
- **LangChain**: 1.1.0+
- **LangGraph**: 1.0.4+
- **google-genai**: 1.52.0+

## 関連ドキュメント

- [はじめての Manganize](../tutorials/getting-started.md) - 基本的な使い方
- [プロンプトをカスタマイズする](../how-to/customize-prompt.md) - プロンプトのカスタマイズ方法
- [アーキテクチャの理解](../explanation/architecture.md) - システムの内部構造

