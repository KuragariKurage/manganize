# Manganize

テキストや URL を「まんがタイムきらら」風 4 コマ漫画に変換する LangGraph エージェント。

## セットアップ

```bash
git clone https://github.com/atsu/manganize.git
cd manganize
uv sync

# Playwright ブラウザのインストール（Web ページ取得用）
uv run playwright install chromium

# API キー設定
export GOOGLE_API_KEY="your-api-key"
```

## 使い方

```bash
# URL から漫画を生成
uv run python main.py "https://example.com/article"

# テキストから漫画を生成
uv run python main.py "Transformerアーキテクチャについて"
```

出力は `output/YYYYMMDD_HHMMSS/` に保存されます。

## アーキテクチャ

3 段階のパイプライン構成：

```
┌──────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Researcher  │ →  │ Scenario Writer │ →  │ Image Generator │
│ (情報収集)   │    │  (脚本作成)     │    │   (画像生成)    │
└──────────────┘    └─────────────────┘    └─────────────────┘
```

- **Researcher**: DuckDuckGo 検索、Web ページ取得、ドキュメント読み取りで情報収集
- **Scenario Writer**: 収集した情報から 4 コマ漫画の脚本を作成
- **Image Generator**: Gemini 3 Pro Image Preview で漫画画像を生成

## プロジェクト構成

```
manganize/
├── manganize/
│   ├── agents.py   # LangGraph エージェント定義
│   ├── tools.py    # ツール（Web 取得、画像生成など）
│   └── prompts.py  # プロンプトテンプレート
├── assets/         # キャラクター参照画像
├── main.py         # CLI エントリーポイント
└── pyproject.toml
```

## 開発

```bash
task lint       # リント
task format     # フォーマット
task typecheck  # 型チェック
```

## 技術スタック

- Python 3.13+ / uv
- LangGraph / LangChain
- Google Generative AI (Gemini)
- Playwright / MarkItDown

## ドキュメント

- [チュートリアル](docs/wiki/tutorials/) - 使い方を学ぶ
- [ハウツー](docs/wiki/how-to/) - 特定の課題を解決
- [リファレンス](docs/wiki/reference/) - API 仕様
- [解説](docs/wiki/explanation/) - 設計思想

## ライセンス

MIT License
