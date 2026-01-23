# AgentCore Runtime 分離 - アーキテクチャ設計

## 概要

ManganizeAgent を AWS Bedrock AgentCore Runtime に分離し、Web アプリとエージェント処理のリソースを独立させる。
Web アプリは HTTP/SSE で AgentCore と通信し、エージェント実行結果を受け取る。

---

## システムアーキテクチャ

### 現在のアーキテクチャ（モノリシック）

```
┌─────────────────────────────────────────────────────────────────┐
│  Web App (FastAPI)                                              │
│  ┌────────────────┐    ┌────────────────────────────────────┐  │
│  │   API Layer    │───▶│       GeneratorService             │  │
│  │   (endpoints)  │    │  ┌──────────────────────────────┐  │  │
│  └────────────────┘    │  │    ManganizeAgent            │  │  │
│                        │  │    (LangGraph 直接実行)       │  │  │
│                        │  └──────────────────────────────┘  │  │
│                        └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 分離後のアーキテクチャ

```
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│   Web App (FastAPI)             │         │   AgentCore Runtime (AWS)       │
│   ─────────────────────         │  HTTP   │   ─────────────────────────     │
│                                 │         │                                 │
│   ┌───────────────────┐         │ POST    │   ┌───────────────────────┐     │
│   │   API Layer       │────────────────────▶  │   BedrockAgentCoreApp │     │
│   │   /api/generate   │         │ /invoke │   │                       │     │
│   └───────────────────┘         │         │   │   @app.entrypoint     │     │
│           │                     │         │   │   def invoke():       │     │
│           ▼                     │         │   │     ManganizeAgent    │     │
│   ┌───────────────────┐         │   SSE   │   │     .generate()       │     │
│   │ GeneratorService  │◀────────────────────  └───────────────────────┘     │
│   │ (AgentCore呼出)   │         │ stream  │             │                   │
│   └───────────────────┘         │         │             ▼                   │
│           │                     │         │   ┌───────────────────────┐     │
│           ▼                     │         │   │   S3 Bucket           │     │
│   ┌───────────────────┐         │         │   │   /characters/        │     │
│   │   DB (SQLite)     │         │         │   │     └─ kurage/        │     │
│   │   - 履歴          │         │         │   │         ├─ portrait   │     │
│   │   - キャラクター   │         │         │   │         └─ full_body  │     │
│   └───────────────────┘         │         │   └───────────────────────┘     │
│                                 │         │                                 │
└─────────────────────────────────┘         └─────────────────────────────────┘
        ▲                                               │
        │                                               │
        └───────────────────────────────────────────────┘
                    生成結果 (image, title)
```

---

## 責務分担

| 責務 | Web App | AgentCore Runtime |
|------|---------|-------------------|
| API エンドポイント | ✅ | - |
| キャラクター CRUD | ✅ | - |
| 履歴 CRUD | ✅ | - |
| 画像保存（DB） | ✅ | - |
| SSE → クライアント配信 | ✅ | - |
| S3 画像アップロード | ✅ | - |
| S3 画像取得 | - | ✅ |
| ManganizeAgent 実行 | - | ✅ |
| リサーチ（DuckDuckGo） | - | ✅ |
| シナリオ生成 | - | ✅ |
| 画像生成（Gemini） | - | ✅ |
| 進捗イベント発行 | - | ✅ |

---

## ディレクトリ構成

```
manganize/
├── manganize/                      # コアエージェント（既存・変更あり）
│   ├── agents.py                   # ManganizeAgent
│   ├── character.py                # BaseCharacter（S3対応追加）
│   ├── tools.py                    # LLM ツール
│   └── prompts.py                  # プロンプト定義
│
├── agentcore/                      # 【新規】AgentCore Runtime
│   ├── main.py                     # BedrockAgentCoreApp エントリーポイント
│   ├── handler.py                  # エージェント実行ハンドラ
│   ├── character_loader.py         # S3 からキャラクター読み込み
│   └── schemas.py                  # リクエスト/レスポンス定義
│
├── web/                            # Web App（変更あり）
│   ├── services/
│   │   ├── generator.py            # 【変更】AgentCore API 呼び出し
│   │   └── character.py            # 【変更】S3 アップロード追加
│   ├── config.py                   # 【変更】AgentCore URL, S3 設定追加
│   └── ...
│
├── infrastructure/                 # 【新規】IaC（オプション）
│   └── cdk/                        # AWS CDK
│       ├── app.py
│       └── stacks/
│           ├── agentcore_stack.py
│           └── s3_stack.py
│
└── pyproject.toml                  # 依存追加
```

---

## API インターフェース

### AgentCore Runtime API

#### POST /invoke

エージェント実行をリクエストし、ストリーミングで進捗・結果を受け取る。

**Request**:
```json
{
  "topic": "Transformerアーキテクチャについて",
  "character_name": "kurage"
}
```

**Response (Streaming)**:
```
event: progress
data: {"type": "progress", "status": "researching", "progress": 20, "message": "リサーチ中..."}

event: progress
data: {"type": "progress", "status": "writing", "progress": 50, "message": "シナリオ作成中..."}

event: progress
data: {"type": "progress", "status": "generating", "progress": 75, "message": "画像生成中..."}

event: result
data: {"type": "result", "image": "<base64>", "title": "Transformer解説"}

```

**Error Response**:
```
event: error
data: {"type": "error", "message": "画像生成に失敗しました", "code": "GENERATION_FAILED"}
```

### Web App → AgentCore 呼び出し

```python
# web/services/generator.py

class GeneratorService:
    async def generate_manga(
        self,
        generation_id: str,
        topic: str,
        character_name: str,
        db_session: DatabaseSession,
    ) -> AsyncGenerator[GenerationStatus, None]:
        """AgentCore Runtime を呼び出してマンガを生成"""

        # AgentCore API を呼び出し
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{settings.agentcore_url}/invoke",
                json={"topic": topic, "character_name": character_name},
                timeout=600.0,  # 10分タイムアウト
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        event = json.loads(line[5:])

                        if event["type"] == "progress":
                            yield GenerationStatus(
                                status=event["status"],
                                progress=event["progress"],
                            )

                        elif event["type"] == "result":
                            # DB に結果を保存
                            image_data = base64.b64decode(event["image"])
                            await db_session.generations.update_with_result(
                                generation_id, image_data, event["title"]
                            )
                            await db_session.commit()

                            yield GenerationStatus(
                                status="completed",
                                progress=100,
                            )

                        elif event["type"] == "error":
                            await db_session.generations.update_error(
                                generation_id, event["message"]
                            )
                            await db_session.commit()
                            raise GenerationError(event["message"])
```

---

## AgentCore Runtime 実装

### エントリーポイント

```python
# agentcore/main.py

from bedrock_agentcore import BedrockAgentCoreApp
from agentcore.handler import AgentHandler

app = BedrockAgentCoreApp()
handler = AgentHandler()

@app.entrypoint
async def invoke(request: dict):
    """エージェント実行エントリーポイント"""
    topic = request.get("topic")
    character_name = request.get("character_name")

    async for event in handler.execute(topic, character_name):
        yield event

app.run()
```

### エージェントハンドラ

```python
# agentcore/handler.py

from manganize.agents import ManganizeAgent
from manganize.character import BaseCharacter
from agentcore.character_loader import load_character_from_s3
import base64

class AgentHandler:
    async def execute(
        self,
        topic: str,
        character_name: str
    ) -> AsyncGenerator[dict, None]:
        """エージェントを実行し、進捗イベントをストリーミング"""

        # S3 からキャラクター情報を取得
        character = await load_character_from_s3(character_name)

        # ManganizeAgent を初期化
        agent = ManganizeAgent(
            character=character,
            researcher_llm=init_chat_model("google_genai:gemini-2.5-pro"),
            scenario_writer_llm=init_chat_model("google_genai:gemini-2.5-flash"),
        )
        graph = agent.compile_graph()

        # ストリーミング実行
        async for chunk in graph.astream(
            {"topic": topic},
            stream_mode="updates"
        ):
            if NodeName.RESEARCHER in chunk:
                yield {
                    "type": "progress",
                    "status": "researching",
                    "progress": 20,
                    "message": "リサーチ中...",
                }

            elif NodeName.SCENARIO_WRITER in chunk:
                yield {
                    "type": "progress",
                    "status": "writing",
                    "progress": 50,
                    "message": "シナリオ作成中...",
                }

            elif NodeName.IMAGE_GENERATOR in chunk:
                yield {
                    "type": "progress",
                    "status": "generating",
                    "progress": 75,
                    "message": "画像生成中...",
                }

        # 最終状態を取得
        final_state = await graph.aget_state(...)

        if final_state.values.get("generated_image"):
            yield {
                "type": "result",
                "image": base64.b64encode(
                    final_state.values["generated_image"]
                ).decode(),
                "title": final_state.values["topic_title"],
            }
        else:
            yield {
                "type": "error",
                "message": "画像生成に失敗しました",
                "code": "GENERATION_FAILED",
            }
```

### S3 キャラクター読み込み

```python
# agentcore/character_loader.py

import boto3
from manganize.character import BaseCharacter

s3_client = boto3.client("s3")
BUCKET_NAME = os.environ.get("CHARACTER_BUCKET_NAME")

async def load_character_from_s3(character_name: str) -> BaseCharacter:
    """S3 からキャラクター情報を取得"""

    # YAML 定義を取得
    yaml_obj = s3_client.get_object(
        Bucket=BUCKET_NAME,
        Key=f"characters/{character_name}/{character_name}.yaml"
    )
    yaml_content = yaml_obj["Body"].read().decode("utf-8")

    # 画像を取得
    portrait_obj = s3_client.get_object(
        Bucket=BUCKET_NAME,
        Key=f"characters/{character_name}/portrait.png"
    )
    portrait_bytes = portrait_obj["Body"].read()

    full_body_obj = s3_client.get_object(
        Bucket=BUCKET_NAME,
        Key=f"characters/{character_name}/full_body.png"
    )
    full_body_bytes = full_body_obj["Body"].read()

    # BaseCharacter を構築
    return BaseCharacter.from_yaml_string(
        yaml_content,
        portrait=portrait_bytes,
        full_body=full_body_bytes,
    )
```

---

## S3 バケット構成

```
manganize-characters-{account-id}/
├── characters/
│   ├── kurage/
│   │   ├── kurage.yaml          # キャラクター定義
│   │   ├── portrait.png         # 顔アップ画像
│   │   └── full_body.png        # 全身画像
│   ├── custom-char-1/
│   │   ├── custom-char-1.yaml
│   │   ├── portrait.png
│   │   └── full_body.png
│   └── ...
```

---

## 設定変更

### web/config.py

```python
class Settings(BaseSettings):
    # 既存設定...

    # 【追加】AgentCore 設定
    agentcore_url: str = "http://localhost:8080"  # ローカル開発時
    agentcore_timeout: int = 600  # 10分

    # 【追加】S3 設定
    character_bucket_name: str = "manganize-characters"
    aws_region: str = "ap-northeast-1"
```

---

## ローカル開発フロー

```bash
# 1. AgentCore Runtime をローカルで起動
cd agentcore
agentcore launch -l
# → http://localhost:8080 で起動

# 2. Web アプリを起動
task dev
# → http://localhost:8000 で起動

# 3. ブラウザでアクセスしてテスト
open http://localhost:8000
```

**注意**: ローカル開発時も S3 へのアクセスが必要（AWS 認証情報が必要）

---

## デプロイメントフロー

### 1. S3 バケット作成（初回のみ）

```bash
aws s3 mb s3://manganize-characters-{account-id} --region ap-northeast-1
```

### 2. デフォルトキャラクターを S3 にアップロード

```bash
aws s3 sync characters/kurage/ s3://manganize-characters-{account-id}/characters/kurage/
```

### 3. AgentCore Runtime をデプロイ

```bash
cd agentcore
agentcore configure -e main.py
agentcore launch
```

### 4. Web アプリの設定を更新

```bash
# .env
AGENTCORE_URL=https://<agentcore-endpoint>.amazonaws.com
CHARACTER_BUCKET_NAME=manganize-characters-{account-id}
```

---

## 依存関係追加

```toml
# pyproject.toml

[project.dependencies]
# 既存...

# 【追加】AgentCore SDK
bedrock-agentcore-sdk-python = ">=0.1.0"

# 【追加】AWS SDK
boto3 = ">=1.35.0"

# 【追加】HTTP クライアント（ストリーミング対応）
httpx = ">=0.27.0"
```

---

## シーケンス図

```
User        Web App                 AgentCore Runtime           S3
 │             │                           │                     │
 │  POST /api/generate                     │                     │
 │  {topic, character}                     │                     │
 │────────────▶│                           │                     │
 │             │                           │                     │
 │             │  POST /invoke             │                     │
 │             │  {topic, char_name}       │                     │
 │             │──────────────────────────▶│                     │
 │             │                           │                     │
 │             │                           │  GET character.yaml │
 │             │                           │────────────────────▶│
 │             │                           │◀────────────────────│
 │             │                           │                     │
 │             │                           │  GET portrait.png   │
 │             │                           │────────────────────▶│
 │             │                           │◀────────────────────│
 │             │                           │                     │
 │             │  SSE: researching         │                     │
 │             │◀──────────────────────────│                     │
 │  SSE        │                           │                     │
 │◀────────────│                           │                     │
 │             │                           │   (LLM calls...)    │
 │             │  SSE: writing             │                     │
 │             │◀──────────────────────────│                     │
 │  SSE        │                           │                     │
 │◀────────────│                           │                     │
 │             │                           │                     │
 │             │  SSE: generating          │                     │
 │             │◀──────────────────────────│                     │
 │  SSE        │                           │                     │
 │◀────────────│                           │                     │
 │             │                           │                     │
 │             │  SSE: result              │                     │
 │             │  {image, title}           │                     │
 │             │◀──────────────────────────│                     │
 │             │                           │                     │
 │             │  DB: save image           │                     │
 │             │────────▶                  │                     │
 │             │                           │                     │
 │  SSE: done  │                           │                     │
 │◀────────────│                           │                     │
 │             │                           │                     │
```

---

## エラーハンドリング

| エラー種別 | 発生箇所 | 対応 |
|-----------|---------|------|
| S3 アクセスエラー | AgentCore | エラーイベント返却、Web でエラー表示 |
| LLM API エラー | AgentCore | リトライ後、エラーイベント返却 |
| タイムアウト | Web ↔ AgentCore | 600秒タイムアウト、エラー表示 |
| ネットワークエラー | Web ↔ AgentCore | リトライ、エラー表示 |
| 不正なリクエスト | AgentCore | 400 エラーレスポンス |

---

## セキュリティ考慮事項

- **認証**: AgentCore Runtime は IAM SigV4 または JWT 認証をサポート
- **通信暗号化**: 本番環境では HTTPS 必須
- **S3 アクセス制御**: AgentCore の IAM ロールにのみ読み取り権限を付与
- **環境変数**: API キー等はシークレットマネージャーで管理
