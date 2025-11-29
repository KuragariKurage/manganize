# はじめての Manganize

このチュートリアルでは、Manganize を使ってテキストコンテンツを漫画画像に変換する基本的な手順を学びます。

## 対象読者

- Python の基本的な知識がある方
- AI を使った画像生成に興味がある方
- LangGraph を学びたい方

## 所要時間

約 15 分

## 前提条件

- Python 3.13 以上がインストールされていること
- `uv` がインストールされていること
- Google Generative AI の API キーを取得していること

## ステップ 1: プロジェクトのセットアップ

まず、リポジトリをクローンして、依存関係をインストールします。

```bash
git clone https://github.com/atsu/manganize.git
cd manganize
uv sync
```

## ステップ 2: API キーの設定

Google Generative AI の API キーを環境変数に設定します。

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

または、`.env` ファイルを作成して API キーを記述します。

```
GOOGLE_API_KEY=your-api-key-here
```

## ステップ 3: 最初の漫画を生成する

`main.py` を実行して、サンプルテキストから漫画を生成してみましょう。

```bash
uv run python main.py
```

このコマンドを実行すると、`transformer.txt` の内容が漫画化され、`generated_image.png` として保存されます。

## ステップ 4: 自分のテキストを漫画化する

独自のテキストを漫画にするには、`main.py` を以下のように編集します。

```python
from io import BytesIO
from pathlib import Path

from langchain.chat_models import init_chat_model
from PIL import Image

from manganize.chain import ManganizeAgent

agent = ManganizeAgent(model=init_chat_model(model="google_genai:gemini-2.5-flash"))

def main():
    # あなたの漫画化したいテキスト
    my_text = """
    今日は良い天気でした。
    公園に行って、友達と遊びました。
    とても楽しい一日でした。
    """

    result = agent(
        f"次のコンテンツをマンガにしてください: {my_text}",
        thread_id="1",
    )

    if result.get("generated_image"):
        image = Image.open(BytesIO(result.get("generated_image")))
        image.save("my_manga.png")
        print("漫画を生成しました: my_manga.png")

if __name__ == "__main__":
    main()
```

## ステップ 5: 生成された画像を確認する

生成された `my_manga.png` を画像ビューアで開いて、結果を確認します。

```bash
# Linux の場合
xdg-open my_manga.png

# macOS の場合
open my_manga.png

# Windows の場合
start my_manga.png
```

## 次のステップ

おめでとうございます！初めての漫画生成に成功しました。

さらに学びたい方は、以下のドキュメントを参照してください：

- [カスタムプロンプトの作成方法](../how-to/customize-prompt.md) - プロンプトをカスタマイズする方法
- [アーキテクチャの理解](../explanation/architecture.md) - システムの内部構造を理解する
- [API リファレンス](../reference/api.md) - 詳細な API 仕様

## トラブルシューティング

### API キーのエラーが出る

`GOOGLE_API_KEY` が正しく設定されているか確認してください。

```bash
echo $GOOGLE_API_KEY
```

### 画像が生成されない

ログを確認して、Gemini API へのリクエストが成功しているか確認してください。API の利用制限に達している可能性もあります。

### 依存関係のインストールに失敗する

`uv` のバージョンが最新であることを確認してください。

```bash
uv self update
```

