# はじめての Manganize

テキストや URL から 4 コマ漫画を生成するための環境構築手順。

## 前提条件

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- [go-task](https://taskfile.dev/)（タスクランナー）
- Node.js（TailwindCSS ビルド用、Web アプリを使う場合のみ）
- Google Generative AI API キー

## セットアップ

### 1. リポジトリのクローンと依存関係のインストール

```bash
git clone https://github.com/atsu/manganize.git
cd manganize
uv sync
uv run playwright install chromium
```

### 2. 環境変数の設定

`.env.example` を `.env` にコピーして、API キーを設定します：

```bash
cp .env.example .env
```

`.env` を編集して `GOOGLE_API_KEY` を設定：

```
GOOGLE_API_KEY=your-api-key
```

API キーは [Google AI Studio](https://aistudio.google.com/app/apikey) で取得できます。

### 3. 初期セットアップ

`task init` で DB マイグレーションとデフォルトキャラクターの登録を一括実行します：

```bash
task init
```

これにより以下が実行されます：

- Alembic マイグレーション（SQLite DB の作成・更新）
- デフォルトキャラクター（くらげちゃん等）のシード

## プロジェクト構成

Manganize は **uv workspace** によるモノレポ構成です：

```
manganize/
├── main.py                  # CLI エントリポイント
├── Taskfile.yml             # タスクランナー設定
├── packages/
│   └── core/                # manganize-core（AI エージェント）
│       └── manganize_core/
│           ├── agents.py    # LangGraph ステートマシン
│           ├── tools.py     # Web スクレイピング、画像生成
│           ├── prompts.py   # システムプロンプト
│           └── character.py # キャラクター定義
├── apps/
│   └── web/                 # manganize-web（Web アプリ）
│       └── manganize_web/
│           ├── main.py      # FastAPI エントリポイント
│           ├── api/         # API エンドポイント
│           ├── models/      # SQLAlchemy モデル
│           ├── services/    # ビジネスロジック
│           └── templates/   # Jinja2 テンプレート
├── characters/              # キャラクター YAML 定義
│   ├── kurage/              # くらげちゃん（デフォルト）
│   └── gpt/                 # GPT キャラクター
└── alembic/                 # DB マイグレーション
```

## CLI で漫画を生成する

```bash
# URL から生成
uv run python main.py "https://example.com/tech-article"

# テキストから生成
uv run python main.py "React Server Components について"

# task コマンドでも実行可能
task run -- "Kubernetes の基本"

# カスタムキャラクターを指定
uv run python main.py -c characters/gpt/gpt.yaml "量子コンピュータについて"
```

出力は `output/YYYYMMDD_HHMMSS/` に以下のファイルが保存されます：

- `generated_image_*.png` - 生成された漫画画像
- `research_results_*.txt` - 調査結果
- `scenario_*.txt` - 生成された脚本

## Web アプリで漫画を生成する

Web アプリを使うと、ブラウザから漫画を生成・管理できます。

```bash
# 開発サーバーの起動（FastAPI + TailwindCSS）
task dev
```

ブラウザで `http://127.0.0.1:8000` にアクセスします。

Web アプリの詳しい使い方は [初めてのマンガを生成する](first-manga.md) を参照してください。

## プログラムから使う

```python
from io import BytesIO

from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from manganize_core.agents import ManganizeAgent
from manganize_core.character import KurageChan
from PIL import Image

# エージェントを初期化してグラフをコンパイル
agent = ManganizeAgent(
    character=KurageChan(),
    researcher_llm=init_chat_model(model="google_genai:gemini-2.5-pro"),
    scenario_writer_llm=init_chat_model(model="google_genai:gemini-2.5-flash"),
    relevance_threshold=0.5,
)
graph = agent.compile_graph()

# 実行
config: RunnableConfig = {"configurable": {"thread_id": "1"}}
result = graph.invoke({"topic": "Kubernetes の基本"}, config)

# 画像を保存
if result.get("generated_image"):
    image = Image.open(BytesIO(result["generated_image"]))
    image.save("manga.png")
```

## 利用可能な task コマンド

```bash
task --list-all    # 全コマンド一覧
task init          # 初期セットアップ（DB + キャラクター）
task dev           # Web アプリ開発サーバー起動
task run           # CLI エージェント実行
task lint          # Ruff リンター
task format        # Ruff フォーマッター
task typecheck     # ty 型チェック
```

## トラブルシューティング

### API キーエラー

```bash
echo $GOOGLE_API_KEY  # 設定されているか確認
```

`.env` ファイルに `GOOGLE_API_KEY` が正しく設定されているか確認してください。

### Playwright エラー

```bash
uv run playwright install chromium
```

### task コマンドが見つからない

[go-task](https://taskfile.dev/) をインストールしてください：

```bash
# macOS
brew install go-task

# Linux
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin
```

### DB マイグレーションエラー

```bash
uv run alembic upgrade head
```

## 次のステップ

- [初めてのマンガを生成する](first-manga.md) - Web アプリの使い方
- [LangGraph を理解する](understanding-langgraph.md) - エージェントの仕組み
- [Reference: API Endpoints](../reference/api-endpoints.md) - API 仕様
