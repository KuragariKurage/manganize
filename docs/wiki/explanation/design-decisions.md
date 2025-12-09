# 設計の意思決定

## 1. LangGraph の採用

### 採用理由

- 状態管理の明確性（`TypedDict` で型安全に管理）
- チェックポイント機能（会話履歴の保存・復元）
- パイプライン構築の柔軟性

### トレードオフ

- LangChain と LangGraph の両方の理解が必要
- シンプルなケースでは過剰な場合がある

## 2. 3 段階パイプライン

### 構成

```
Researcher → Scenario Writer → Image Generator
```

### 採用理由

- 各段階で特化したプロンプトと LLM を使える
- デバッグしやすい（中間出力を確認可能）
- 各コンポーネントを独立してテスト・改善可能

### トレードオフ

- API 呼び出しが複数回発生（コスト・レイテンシ）
- シンプルなユースケースでは過剰

## 3. Gemini 3 Pro Image Preview

### 採用理由

- マルチモーダル入力（テキスト + 参照画像）
- プロンプトで詳細なスタイル制御が可能
- Google Search 連携（リアルタイム情報取得）

### トレードオフ

- プレビュー版のため API 変更の可能性
- Google のポリシーに依存

## 4. 型ヒントの徹底

### 採用理由

- バグの早期発見
- コードの意図が明確になる
- IDE サポート（補完、リファクタリング）

```python
def _researcher_node(self, state: ManganizeAgentState) -> Command:
    ...
```

## 5. uv によるパッケージ管理

### 採用理由

- Rust 実装による高速なパッケージ解決
- シンプルな設定（pyproject.toml）
- lockfile による再現可能なビルド

### ベンチマーク

| ツール | インストール時間 |
|--------|----------------|
| pip | 30 秒 |
| uv | 5 秒 |

## 6. InMemorySaver の選択

### 現在の採用理由

- シンプル（追加依存なし）
- 開発速度（セットアップ不要）
- テスト容易性

### 本番環境での推奨

```python
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver(connection_string=os.getenv("DATABASE_URL"))
```

## 7. ディレクトリ構造

```
manganize/
├── manganize/
│   ├── agents.py   # エージェント定義
│   ├── tools.py    # ツール
│   └── prompts.py  # プロンプト
├── main.py
└── assets/
```

### 採用理由

- 小規模プロジェクトに適したフラット構造
- 新規参加者が理解しやすい

## 8. エラーハンドリング

### 方針

ツール内で例外をキャッチし、`None` を返す。エージェントを停止させない。

```python
if image_parts:
    return image_data
return None  # 失敗時
```

### 採用理由

- エージェントが継続可能
- エラーもログに記録される
