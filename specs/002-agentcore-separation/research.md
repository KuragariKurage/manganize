# AgentCore Runtime 調査結果

## 概要

Amazon Bedrock AgentCore Runtime は、AI エージェントをデプロイ・スケーリングするためのサーバーレスランタイム。
フレームワーク非依存（LangGraph、CrewAI、Strands 等）で、任意の LLM プロバイダ（Gemini 含む）を利用可能。

## 主要な特徴

| 特徴 | 説明 |
|------|------|
| **サーバーレス** | インフラ管理不要、自動スケーリング |
| **セッション分離** | 各セッションは独立したマイクロ VM で実行 |
| **フレームワーク非依存** | LangGraph、CrewAI、Strands 等をサポート |
| **モデル非依存** | Bedrock、OpenAI、Gemini 等の任意のモデルを利用可能 |
| **従量課金** | 実際の処理時間のみ課金（LLM 待ち時間は課金外） |
| **ストリーミング対応** | HTTP API および WebSocket 接続をサポート |

## SDK 基本パターン

```python
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(request):
    topic = request.get("topic")
    result = my_agent.process(topic)
    return {"result": result}

app.run()
```

## ローカル開発

### コマンド

```bash
# ローカルでビルド・起動
agentcore launch -l

# → http://localhost:8080 で起動
# → Docker コンテナとして実行
```

### 要件

- Docker（または Finch、Podman）が必要
- AWS 認証情報（S3 等へのアクセス用）

### テスト

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"topic": "Transformerについて", "character_name": "kurage"}'
```

## デプロイメント方式

### 1. Direct Code Deployment（推奨・高速）

```bash
# ZIP ファイルでデプロイ（Docker/ECR 不要）
agentcore configure -e main.py
agentcore launch
```

- 高速なイテレーション
- コンテナビルド不要
- プロトタイピングに最適

### 2. Container-Based Deployment

```bash
# Dockerfile からコンテナビルド → ECR → デプロイ
agentcore launch --container
```

- 本番環境向け
- カスタム依存関係が必要な場合

## LangGraph 統合

### メモリ統合

```python
from langgraph_checkpoint_aws import AgentCoreMemorySaver

# チェックポインターとして使用
graph = agent.compile(checkpointer=AgentCoreMemorySaver())
```

### 既存エージェントの統合

LangGraph で構築した既存エージェントは、`@app.entrypoint` でラップするだけで統合可能。

```python
from bedrock_agentcore import BedrockAgentCoreApp
from manganize.agents import ManganizeAgent

app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(request):
    agent = ManganizeAgent(...)
    graph = agent.compile_graph()

    async for chunk in graph.astream({"topic": request["topic"]}):
        yield process_chunk(chunk)

app.run()
```

## AgentCore コンポーネント

| コンポーネント | 機能 | 今回の利用 |
|---------------|------|-----------|
| **Runtime** | エージェント実行環境 | ✅ 使用 |
| **Gateway** | API を MCP ツールに変換 | - |
| **Identity** | 認証・認可管理 | 将来検討 |
| **Memory** | 永続化メモリ | 将来検討 |
| **Tools** | コードインタプリタ、ブラウザ | - |
| **Observability** | OpenTelemetry トレーシング | 将来検討 |

## 料金体系

- **従量課金**: 実際に処理した時間のみ課金
- **LLM 待ち時間**: 課金対象外（コスト効率が良い）
- **最小課金単位**: 調査中

## リージョン対応

- GA 済み: us-east-1, us-west-2
- ap-northeast-1: 確認中（ユーザー情報では利用可能とのこと）

## 参考リンク

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/)
- [AgentCore Samples (GitHub)](https://github.com/awslabs/amazon-bedrock-agentcore-samples)
- [AgentCore SDK Python (GitHub)](https://github.com/aws/bedrock-agentcore-sdk-python)
- [AgentCore Starter Toolkit](https://aws.github.io/bedrock-agentcore-starter-toolkit/)
- [Runtime Quickstart](https://aws.github.io/bedrock-agentcore-starter-toolkit/user-guide/runtime/quickstart.html)
