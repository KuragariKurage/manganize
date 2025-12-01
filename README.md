# Manganize

テキストコンテンツをマンガ画像に変換する LangGraph ベースの AI エージェント

## 概要

Manganize は、Google Generative AI (Gemini) を使用して、テキストコンテンツを「まんがタイムきらら」風の萌え系日常4コマ漫画に変換するシステムです。LangGraph と LangChain を活用したエージェントアーキテクチャで構築されています。

## 特徴

- 🎨 **高品質な漫画生成**: Gemini 3 Pro Image Preview による美しい漫画スタイル
- 🤖 **LangGraph エージェント**: 会話履歴を維持する賢いエージェント
- 📝 **カスタマイズ可能**: プロンプトやスタイルを簡単にカスタマイズ
- 🔧 **拡張可能**: 独自のツールを簡単に追加できる設計
- 🐍 **型安全**: mypy による静的型チェック完備

## クイックスタート

### 前提条件

- Python 3.13 以上
- [uv](https://github.com/astral-sh/uv) がインストールされていること
- Google Generative AI の API キー

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/atsu/manganize.git
cd manganize

# 依存関係をインストール
uv sync
```

### 設定

Google Generative AI の API キーを環境変数に設定します。

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

または、`.env` ファイルを作成：

```bash
echo "GOOGLE_API_KEY=your-api-key-here" > .env
```

### 実行

```bash
uv run python main.py
```

生成された漫画は `generated_image.png` として保存されます。

## 基本的な使い方

```python
from manganize.chain import ManganizeAgent
from PIL import Image
from io import BytesIO

# エージェントを初期化
agent = ManganizeAgent()

# テキストを漫画に変換
result = agent(
    "猫が魚を見つけて喜ぶストーリー",
    thread_id="story-001",
)

# 画像を保存
if result.get("generated_image"):
    image = Image.open(BytesIO(result["generated_image"]))
    image.save("my_manga.png")
```

## ドキュメント

詳細なドキュメントは [Wiki](docs/wiki/) をご覧ください。

### 📚 [Tutorials（チュートリアル）](docs/wiki/tutorials/)

学習指向 - 初めての方向けの手順書

- [はじめての Manganize](docs/wiki/tutorials/getting-started.md)
- [LangGraph を理解する](docs/wiki/tutorials/understanding-langgraph.md)

### 🛠️ [How-to Guides（ハウツーガイド）](docs/wiki/how-to/)

問題解決指向 - 特定の課題を解決する方法

- [プロンプトをカスタマイズする](docs/wiki/how-to/customize-prompt.md)
- [カスタムツールを追加する](docs/wiki/how-to/add-custom-tool.md)
- [画像品質を最適化する](docs/wiki/how-to/optimize-image-quality.md)

### 📖 [Reference（リファレンス）](docs/wiki/reference/)

情報指向 - 技術仕様と API ドキュメント

- [API リファレンス](docs/wiki/reference/api.md)
- [設定リファレンス](docs/wiki/reference/configuration.md)

### 🧠 [Explanation（解説）](docs/wiki/explanation/)

理解指向 - システムの背景と設計思想

- [アーキテクチャ解説](docs/wiki/explanation/architecture.md)
- [設計の意思決定](docs/wiki/explanation/design-decisions.md)
- [プロンプトエンジニアリング解説](docs/wiki/explanation/prompt-engineering.md)

## プロジェクト構成

```
manganize/
├── manganize/          # メインパッケージ
│   ├── chain.py        # LangGraph エージェント定義
│   ├── tools.py        # エージェントが使用するツール
│   └── prompts.py      # プロンプトテンプレート
├── assets/             # 静的ファイル（キャラクター画像など）
├── docs/               # ドキュメント
│   ├── specs/          # 機能仕様（Spec 駆動開発）
│   └── wiki/           # 技術ドキュメント（Divio システム）
├── main.py             # エントリーポイント
├── pyproject.toml      # プロジェクト設定
└── AGENTS.md           # AI エージェント向けガイド
```

## 開発

### リント・フォーマット

```bash
# リント
uv run ruff check .

# フォーマット
uv run ruff format .

# 型チェック
uv run mypy manganize/
```

### タスクランナー（Task）

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

## 技術スタック

- **言語**: Python 3.13+
- **パッケージ管理**: uv
- **フレームワーク**: LangGraph / LangChain
- **LLM**: Google Generative AI (Gemini)
- **開発ツール**: mypy（型チェック）, ruff（リント・フォーマット）

## Spec 駆動開発

このプロジェクトでは、仕様と実装の同期を保つために **Spec 駆動開発** を採用しています。詳細は [AGENTS.md](AGENTS.md) を参照してください。

## ライセンス

[MIT License](LICENSE)

## 貢献

Issue や Pull Request を歓迎します。貢献する前に以下をご確認ください：

- [AGENTS.md](AGENTS.md) - AI エージェント向け開発ガイド
- [Constitution](.specify/memory/constitution.md) - プロジェクトの根本原則とガバナンスモデル

## 関連リンク

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Generative AI Documentation](https://ai.google.dev/gemini-api/docs)

