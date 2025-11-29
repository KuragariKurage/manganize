# Reference（リファレンス）

**情報指向** - Manganize の技術仕様と API ドキュメントです。

リファレンスは、機能の詳細な説明と正確な仕様を提供します。特定の API や設定項目を確認したいときに参照してください。

## 📖 利用可能なリファレンス

### API リファレンス

[API リファレンス →](api.md)

**内容**:

#### ManganizeAgent
- `__init__(model)` - エージェントの初期化
- `__call__(input_text, thread_id)` - エージェントの実行

#### Tools
- `generate_manga_image(content, runtime)` - 漫画画像生成ツール

#### Prompts
- `MANGANIZE_AGENT_SYSTEM_PROMPT` - システムプロンプト

#### 型定義
- `ManganizeAgentState` - エージェントの状態
- `BaseChatModel` - 言語モデルの基底クラス
- `Command` - ツールの実行結果
- `ToolRuntime` - ツールのランタイム
- `ImageConfig` - 画像生成設定
- `GenerateContentConfig` - コンテンツ生成設定

#### エラーハンドリング
- 一般的なエラーと解決方法
- 環境変数の設定

#### 使用例
- 基本的な使用例
- 会話を続ける例
- カスタムモデルを使用する例

---

### 設定リファレンス

[設定リファレンス →](configuration.md)

**内容**:

#### プロジェクト設定
- `pyproject.toml` - プロジェクトメタデータと依存関係
- `langgraph.json` - LangGraph の設定
- `.env` - 環境変数

#### ツール設定
- `Taskfile.yml` - タスクランナーの設定

#### Ruff 設定
- `ruff.toml` - リント・フォーマット設定
- ルールカテゴリの説明

#### Mypy 設定
- `mypy.ini` または `pyproject.toml` - 型チェック設定
- 主要なオプション

#### ログ設定
- Python の logging モジュールの設定
- ログレベルの説明

#### デプロイ設定
- `Dockerfile` - Docker イメージの構築
- `docker-compose.yml` - Docker Compose の設定

---

## リファレンスの使い方

### 1. 特定の API を調べる

```
目的: generate_manga_image の使い方を知りたい
  ↓
API リファレンス → Tools → generate_manga_image
  ↓
パラメータ、戻り値、例を確認
```

### 2. 環境変数を確認する

```
目的: GOOGLE_API_KEY の設定方法を知りたい
  ↓
API リファレンス → 環境変数
  ↓
または
設定リファレンス → プロジェクト設定 → .env
```

### 3. 設定ファイルの形式を確認する

```
目的: pyproject.toml の書き方を知りたい
  ↓
設定リファレンス → プロジェクト設定 → pyproject.toml
  ↓
フィールドの説明と例を確認
```

## クイックリファレンス

よく使われる API と設定の概要です。

### ManganizeAgent の基本的な使い方

```python
from manganize.chain import ManganizeAgent

agent = ManganizeAgent()
result = agent("テキストコンテンツ", thread_id="1")

if result.get("generated_image"):
    # 画像データを処理
    image_data = result["generated_image"]
```

### 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `GOOGLE_API_KEY` | Google Generative AI の API キー | ✓ |
| `LANGCHAIN_TRACING_V2` | LangSmith トレーシング | - |
| `LANGCHAIN_API_KEY` | LangSmith の API キー | - |

### 画像生成パラメータ

| パラメータ | 値 | 説明 |
|-----------|-----|------|
| `aspect_ratio` | `"1:1"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"` | アスペクト比 |
| `image_size` | `"1K"`, `"2K"`, `"4K"` | 画像サイズ |

### タスクコマンド

```bash
# リント
task lint

# フォーマット
task format

# 型チェック
task typecheck

# 実行
task run
```

## リファレンスとその他のドキュメントの関係

```
Tutorial（チュートリアル）
  ↓ 基本的な使い方を学ぶ

Reference（リファレンス） ← あなたはここ
  ↓ 詳細な仕様を確認する

How-to（ハウツーガイド）
  ↓ 実践的な問題を解決する

Explanation（解説）
  ↓ 設計思想を理解する
```

## 関連ドキュメント

### 学習の準備

- [はじめての Manganize](../tutorials/getting-started.md) - 基本的な使い方
- [LangGraph を理解する](../tutorials/understanding-langgraph.md) - 内部の仕組み

### 実践的なガイド

- [プロンプトをカスタマイズする](../how-to/customize-prompt.md) - プロンプトの編集
- [カスタムツールを追加する](../how-to/add-custom-tool.md) - ツールの追加
- [画像品質を最適化する](../how-to/optimize-image-quality.md) - 画質の向上

### 理解を深める

- [アーキテクチャ解説](../explanation/architecture.md) - システムの構造
- [設計の意思決定](../explanation/design-decisions.md) - 技術選定の背景
- [プロンプトエンジニアリング解説](../explanation/prompt-engineering.md) - プロンプト設計

## バージョン情報

このリファレンスは、以下のバージョンに基づいています。

- **Manganize**: 0.1.0
- **Python**: 3.13+
- **LangChain**: 1.1.0+
- **LangGraph**: 1.0.4+
- **google-genai**: 1.52.0+

## フィードバック

リファレンスに関するフィードバックや質問は、GitHub の Issue でお願いします。

- 不足している情報
- 不正確な記述
- 追加してほしい API や設定項目

## 貢献

新しい API や設定項目を追加した場合は、このリファレンスも更新してください。

1. API を実装する
2. リファレンスに仕様を記述する
3. 使用例を追加する
4. Pull Request を作成する

