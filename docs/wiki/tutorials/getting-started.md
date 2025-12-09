# はじめての Manganize

テキストや URL から漫画を生成する基本手順。

## 前提条件

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- Google Generative AI API キー

## セットアップ

```bash
git clone https://github.com/atsu/manganize.git
cd manganize
uv sync
uv run playwright install chromium
```

API キーを設定：

```bash
export GOOGLE_API_KEY="your-api-key"
```

## 漫画を生成する

```bash
# URL から生成
uv run python main.py "https://example.com/tech-article"

# テキストから生成
uv run python main.py "React Server Components について"
```

出力は `output/YYYYMMDD_HHMMSS/` に以下のファイルが保存されます：

- `generated_image_*.png` - 生成された漫画画像
- `research_results_*.txt` - 調査結果
- `scenario_*.txt` - 生成された脚本

## プログラムから使う

```python
from io import BytesIO
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from PIL import Image

from manganize.agents import ManganizeAgent

# エージェントを初期化してグラフをコンパイル
agent = ManganizeAgent(
    model=init_chat_model(model="google_genai:gemini-2.5-flash")
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

## トラブルシューティング

### API キーエラー

```bash
echo $GOOGLE_API_KEY  # 設定されているか確認
```

### Playwright エラー

```bash
uv run playwright install chromium
```

## 次のステップ

- [プロンプトをカスタマイズする](../how-to/customize-prompt.md)
- [アーキテクチャ解説](../explanation/architecture.md)
