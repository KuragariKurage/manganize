# アーキテクチャ解説

このドキュメントは、Manganize のシステムアーキテクチャと設計思想を解説します。

## システム概要

Manganize は、テキストコンテンツをマンガ画像に変換する AI エージェントシステムです。以下の技術スタックで構成されています。

```
┌─────────────────────────────────────────┐
│         ユーザーインターフェース          │
│              (main.py)                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       ManganizeAgent (chain.py)         │
│    ┌─────────────────────────────┐     │
│    │   LangGraph エージェント     │     │
│    │  - 状態管理                  │     │
│    │  - ツール呼び出し             │     │
│    │  - 会話履歴管理               │     │
│    └─────────────────────────────┘     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│        ツール層 (tools.py)              │
│  ┌────────────────────────────────┐    │
│  │  generate_manga_image           │    │
│  │  - プロンプト構築                │    │
│  │  - 画像生成リクエスト            │    │
│  │  - 結果の処理                   │    │
│  └────────────────────────────────┘    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│     Google Generative AI API            │
│    (Gemini 3 Pro Image Preview)         │
│  - テキスト → 画像変換                   │
│  - スタイル適用                          │
│  - Google Search 連携                    │
└─────────────────────────────────────────┘
```

## コアコンポーネント

### 1. ManganizeAgent（エージェント層）

**役割**: システムの中核として、ユーザーの入力を受け取り、適切なツールを呼び出して処理を実行します。

**責務**:
- ユーザー入力の受付
- LLM による意図理解と計画
- ツールの選択と実行
- 会話履歴の管理
- 最終結果の返却

**設計の特徴**:

#### 状態管理

LangGraph の `AgentState` を継承して、エージェントの状態を管理します。

```python
class ManganizeAgentState(AgentState):
    generated_image: Optional[bytes]
```

この設計により、以下が可能になります：

- **明示的な状態**: 何が状態に含まれるか型で明示
- **型安全性**: mypy による静的型チェック
- **拡張性**: 新しい状態フィールドを簡単に追加

#### チェックポイント機能

`InMemorySaver` を使用して、会話履歴と状態をメモリに保存します。

```python
checkpointer=InMemorySaver()
```

これにより、同じ `thread_id` を使った連続的な会話が可能になります。

**設計の理由**:

- **メモリ効率**: 永続化が不要な場合に適している
- **シンプル性**: 追加の依存関係が不要
- **テスト容易性**: 状態のリセットが簡単

**代替案**:

本番環境では、以下のチェックポインターが推奨されます：

```python
from langgraph.checkpoint.postgres import PostgresSaver

# PostgreSQL を使った永続化
checkpointer = PostgresSaver(connection_string="postgresql://...")
```

### 2. ツール層

**役割**: エージェントが実行できる具体的な機能を提供します。

#### generate_manga_image ツール

**責務**:
- プロンプトの構築
- Gemini API の呼び出し
- 画像データの抽出と検証
- エラーハンドリング

**処理フロー**:

```
1. content を受け取る
   ↓
2. プロンプトテンプレートに content を埋め込む
   ↓
3. キャラクター参照画像を読み込む
   ↓
4. Gemini API にリクエストを送信
   ↓
5. レスポンスから画像データを抽出
   ↓
6. Command オブジェクトで状態を更新
```

**設計のポイント**:

```python
return Command(
    update={
        "generated_image": image_data,
        "messages": [ToolMessage(...)]
    }
)
```

`Command` オブジェクトを返すことで、LangGraph のグラフ内で状態が適切に更新されます。

**エラーハンドリング**:

```python
if image_parts:
    # 成功ケース
    return Command(update={"generated_image": image_data, ...})

# 失敗ケース
return Command(update={"generated_image": None, ...})
```

明示的に失敗ケースを処理し、エージェントがエラーから回復できるようにしています。

### 3. プロンプト層

**役割**: LLM に対する指示を定義します。

**構造**:

```
MANGANIZE_AGENT_SYSTEM_PROMPT
├─ Role: 作家の役割定義
├─ Character Reference: キャラクター仕様
├─ Art Style & Layout: スタイルと構成
├─ Negative Constraints: 禁止事項
└─ Content / Story: {content} プレースホルダー
```

**設計思想**:

1. **明確な役割定義**: LLM に具体的なペルソナを与える
2. **詳細な制約**: 期待する出力の品質を保証
3. **構造化**: セクションごとに整理して可読性を向上
4. **テンプレート化**: `{content}` でコンテンツを動的に挿入

**プロンプトエンジニアリングの原則**:

- **具体性**: 曖昧な表現を避け、具体的な指示を記述
- **制約の明示**: やってほしいことだけでなく、やってほしくないことも記述
- **例の提供**: 可能であれば、期待する出力の例を示す

## データフロー

### 1. 基本的な実行フロー

```
User Input (テキスト)
    ↓
ManganizeAgent.__call__()
    ↓
LangGraph エージェント
    ├─ ユーザー入力を解析
    ├─ generate_manga_image ツールを選択
    └─ ツールを実行
        ↓
generate_manga_image()
    ├─ プロンプトを構築
    ├─ Gemini API を呼び出し
    └─ 画像データを取得
        ↓
Command による状態更新
    ├─ generated_image: bytes
    └─ messages: [ToolMessage]
        ↓
エージェントが結果を返却
    ↓
User (画像データを受け取る)
```

### 2. 会話履歴の管理

```
Request 1 (thread_id="story-001")
    ↓
InMemorySaver に保存
    ├─ messages: [HumanMessage, AIMessage, ToolMessage, ...]
    └─ generated_image: bytes
        ↓
Request 2 (thread_id="story-001", 同じ ID)
    ↓
InMemorySaver から履歴を復元
    ├─ 以前の会話を参照
    └─ コンテキストを維持
```

## 設計パターン

### 1. ツールパターン

LangChain の `@tool` デコレータを使用して、関数をツール化します。

```python
@tool
def my_tool(input: str, runtime: ToolRuntime) -> Command:
    """ツールの説明。"""
    result = process(input)
    return Command(update={"key": result})
```

**利点**:

- **宣言的**: デコレータで簡潔に定義
- **型安全**: 型ヒントが必須
- **ドキュメント化**: docstring が自動的に LLM に渡される

### 2. 状態更新パターン

`Command` オブジェクトで状態を更新します。

```python
return Command(
    update={
        "field1": value1,
        "field2": value2,
        "messages": [ToolMessage(...)]
    }
)
```

**利点**:

- **不変性**: 既存の状態を変更せず、新しい状態を作成
- **追跡可能**: 状態の変更履歴を追跡できる
- **並行性**: 複数のツールが並行実行できる

### 3. チェックポイントパターン

会話の状態をチェックポイントに保存します。

```python
checkpointer = InMemorySaver()

config = {"configurable": {"thread_id": thread_id}}
agent.invoke(messages, config)
```

**利点**:

- **会話の継続**: 複数のリクエストで会話を維持
- **ロールバック**: 前の状態に戻すことができる（実装次第）
- **デバッグ**: 状態の履歴を確認できる

## スケーラビリティの考慮

### 現在のアーキテクチャの制限

1. **メモリベースのチェックポイント**:
   - サーバー再起動で会話履歴が失われる
   - 複数プロセスで状態を共有できない

2. **同期実行**:
   - 画像生成が完了するまで待機
   - 複数のリクエストを並行処理できない

3. **スケールアウトの課題**:
   - 状態がメモリに保存されるため、水平スケールが困難

### 改善案

#### 1. 永続化チェックポインター

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver(
    connection_string=os.getenv("DATABASE_URL")
)
```

**利点**:
- 会話履歴の永続化
- 複数プロセスでの状態共有
- 障害時の復旧

#### 2. 非同期実行

```python
import asyncio

class ManganizeAgent:
    async def __call__(self, input_text: str, thread_id: str):
        response = await self.agent.ainvoke(messages, config)
        return response
```

**利点**:
- 複数リクエストの並行処理
- レスポンス時間の改善

#### 3. キュー/ワーカーパターン

```
API サーバー → メッセージキュー → ワーカー → Gemini API
                (Redis/RabbitMQ)    (複数プロセス)
```

**利点**:
- 負荷分散
- スケーラビリティ
- 非同期処理

## セキュリティの考慮

### API キーの管理

**現在**:

```python
client = genai.Client()  # 環境変数から自動取得
```

**推奨**:

```python
import os

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY が設定されていません")

client = genai.Client(api_key=api_key)
```

### 入力の検証

**現在**: 入力の検証がない

**推奨**:

```python
def validate_content(content: str) -> str:
    """コンテンツを検証する。"""
    if not content or not content.strip():
        raise ValueError("コンテンツが空です")

    if len(content) > 10000:
        raise ValueError("コンテンツが長すぎます（最大 10,000 文字）")

    return content.strip()
```

### レート制限

**推奨**:

```python
from time import sleep, time

class RateLimiter:
    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = window
        self.requests = []

    def acquire(self):
        now = time()
        self.requests = [t for t in self.requests if now - t < self.window]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.window - (now - self.requests[0])
            sleep(sleep_time)

        self.requests.append(time())
```

## テスタビリティ

### ユニットテスト

```python
# tests/test_tools.py

def test_generate_manga_image():
    from manganize.tools import generate_manga_image

    # モックを使用
    with patch("manganize.tools.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.return_value = ...

        result = generate_manga_image.invoke({"content": "test"})

        assert result is not None
        assert result.update["generated_image"] is not None
```

### 統合テスト

```python
# tests/test_agent.py

def test_manganize_agent():
    agent = ManganizeAgent()

    result = agent(
        "簡単なテストストーリー",
        thread_id="test-001",
    )

    assert "generated_image" in result
    assert result["generated_image"] is not None
```

### モックの活用

API 呼び出しをモックして、テストを高速化・安定化します。

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_gemini_client():
    with patch("manganize.tools.genai.Client") as mock:
        # レスポンスを設定
        mock_response = MagicMock()
        mock_response.parts = [
            MagicMock(inline_data=MagicMock(data=b"fake_image_data"))
        ]
        mock.return_value.models.generate_content.return_value = mock_response

        yield mock
```

## まとめ

Manganize のアーキテクチャは、以下の原則に基づいて設計されています。

1. **関心の分離**: エージェント、ツール、プロンプトを分離
2. **拡張性**: 新しいツールやプロンプトを簡単に追加
3. **型安全性**: 型ヒントによる静的型チェック
4. **テスト容易性**: モックを使った単体テスト
5. **シンプル性**: 必要最小限の依存関係

今後の改善として、以下が検討されます。

- 永続化チェックポインターの導入
- 非同期実行のサポート
- キュー/ワーカーパターンの実装
- 包括的な入力検証とエラーハンドリング

## 関連ドキュメント

- [API リファレンス](../reference/api.md) - API の詳細仕様
- [LangGraph を理解する](../tutorials/understanding-langgraph.md) - LangGraph の基礎
- [設計の背景](design-decisions.md) - 設計の意思決定の背景

