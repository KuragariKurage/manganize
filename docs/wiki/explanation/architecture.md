# アーキテクチャ解説

## システム概要

```
┌─────────────┐
│   main.py   │ CLI エントリーポイント
└──────┬──────┘
       │ topic (URL/テキスト)
       ▼
┌──────────────────────────────────────────────────────────────┐
│                    ManganizeAgent                            │
│  ┌────────────┐   ┌─────────────────┐   ┌────────────────┐  │
│  │ Researcher │ → │ Scenario Writer │ → │Image Generator │  │
│  │            │   │                 │   │                │  │
│  │ DuckDuckGo │   │ 4コマ脚本作成   │   │ Gemini 3 Pro   │  │
│  │ Playwright │   │                 │   │ Image Preview  │  │
│  │ MarkItDown │   │                 │   │                │  │
│  └────────────┘   └─────────────────┘   └────────────────┘  │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
   generated_image (PNG)
```

## パイプライン

### 1. Researcher

入力トピックから情報を収集し、構造化されたファクトシートを作成。

**使用ツール**:
- `DuckDuckGoSearchRun`: Web 検索
- `retrieve_webpage`: URL から Markdown 取得
- `read_document_file`: ドキュメント読み取り

**出力**: 技術要点、エンジニアへのインパクト、シナリオ構成案

### 2. Scenario Writer

ファクトシートを元に 4 コマ漫画の脚本を作成。

**キャラクター**: くらがりくらげ（クールな美少女エンジニア）

**出力形式**:
```
【1コマ目】
* 状況: ...
* 視覚的指示: ...
* セリフ: くらげ「...」
```

### 3. Image Generator

脚本から「まんがタイムきらら」風の漫画画像を生成。

- キャラクター参照画像を入力
- 9:16 アスペクト比、2K 解像度

## 状態管理

LangGraph の StateGraph で状態を管理：

```python
class ManganizeAgentState(TypedDict):
    topic: str              # 入力
    research_results: str   # Researcher 出力
    scenario: str           # Scenario Writer 出力
    generated_image: bytes  # Image Generator 出力
```

`InMemorySaver` でチェックポイントを保存し、会話履歴を維持。

## データフロー

```
topic
  ↓
Researcher.invoke(topic)
  ↓
research_results
  ↓
ScenarioWriter.invoke(research_results)
  ↓
scenario
  ↓
generate_manga_image(scenario)
  ↓
generated_image
```

## 拡張ポイント

- **モデル変更**: コンストラクタで `model` を指定
- **プロンプト変更**: `prompts.py` を編集
- **ツール追加**: `tools.py` にツールを追加し、Researcher に登録
- **永続化**: `InMemorySaver` を `PostgresSaver` 等に置換
