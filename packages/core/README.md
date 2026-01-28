# manganize-core

LangGraph ベースの AI エージェントコアパッケージ。テキストコンテンツを「まんがタイムきらら」風の4コマ漫画に変換します。

## 概要

このパッケージは、以下の3つの LangGraph エージェントを提供します：

1. **Researcher Agent**: トピックに関する情報を収集し、ファクトシートを作成
2. **Scenario Writer Agent**: 収集した情報から4コマ漫画の脚本を作成
3. **Image Generator Agent**: 脚本をもとにマンガ画像を生成

## 主要モジュール

| モジュール | 説明 |
|-----------|------|
| `agents.py` | LangGraph エージェントの定義とグラフ構築 |
| `tools.py` | Web スクレイピング、ドキュメント読取、画像生成ツール |
| `prompts.py` | 各エージェント用のシステムプロンプトテンプレート |
| `character.py` | キャラクター基底クラスと定義 |

## 依存パッケージ

- **LangGraph / LangChain**: エージェントフレームワーク
- **Google Generative AI (Gemini)**: LLM プロバイダー
- **Playwright**: Web スクレイピング
- **MarkItDown**: ドキュメント読み取り（PDF, Word, Excel 等）
- **Pillow**: 画像処理
- **DuckDuckGo Search**: Web 検索

## 使用例

```python
from manganize_core.agents import ManganizeAgent
from manganize_core.character import KurageChan

# エージェントを作成
agent = ManganizeAgent(character=KurageChan())
graph = agent.compile_graph()

# 同期実行
result = graph.invoke({"topic": "Transformerアーキテクチャについて"})

# 非同期実行
async for chunk in graph.astream(
    {"topic": "https://example.com/article"},
    stream_mode="updates"
):
    print(chunk)
```

## 環境変数

| 変数名 | 説明 | 必須 |
|-------|------|------|
| `GOOGLE_API_KEY` | Google Generative AI の API キー | ✅ |

API キーの取得: https://aistudio.google.com/app/apikey

## 開発

```bash
# パッケージのインストール
cd packages/core
uv sync

# 型チェック
uv run ty manganize_core

# リント
uv run ruff check manganize_core
```
