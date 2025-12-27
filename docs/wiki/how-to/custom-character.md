# カスタムキャラクターの作成と使用

このガイドでは、manganizeで独自のキャラクターを作成し、使用する方法を説明します。

## 概要

manganizeでは、デフォルトの「くらげちゃん」以外にも、任意のキャラクターを使ってマンガを生成できます。キャラクターは以下の2つの方法で定義できます：

1. **YAMLファイル**から読み込む（推奨）
2. **Pythonコード**で直接定義する

## YAMLファイルでキャラクターを定義する

### 1. キャラクター設定ファイルの作成

`characters/` ディレクトリに新しいYAMLファイルを作成します。

```yaml
# characters/my_character.yaml
name: キャラクターの正式名称
nickname: 愛称
attributes:
  - 属性1（例：天才ハッカー）
  - 属性2（例：セキュリティ専門家）
personality: キャラクターの性格や振る舞いの説明

speech_style:
  tone: 話し方の基本トーン（例：明るく元気な話し方）
  patterns:
    - "～だよ"
    - "～ね"
    - "～かな"
  examples:
    - "これ面白いよ！"
    - "なるほどね"
  forbidden:
    - "堅苦しい敬語"
    - "古風な言い回し"

images:
  portrait: path/to/portrait.png  # 顔アップ画像（YAMLファイルからの相対パス）
  full_body: path/to/fullbody.png # 全身画像（YAMLファイルからの相対パス）
```

### 2. 画像の準備

キャラクターには2種類の画像が必要です：

- **portrait（顔アップ）**: キャラクターの顔がはっきり見える画像
- **full_body（全身）**: キャラクターの全身が写っている画像

画像は PNG 形式を推奨します。

### 3. キャラクターを使ってマンガを生成

コマンドラインから `--character` オプションでYAMLファイルを指定します：

```bash
python main.py "技術トピック" --character characters/my_character.yaml
```

## Pythonコードでキャラクターを定義する

### 1. キャラクタークラスの作成

`manganize/character.py` に新しいクラスを追加します：

```python
from pathlib import Path
from manganize.character import BaseCharacter, SpeechStyle

class MyCharacter(BaseCharacter):
    """カスタムキャラクター"""

    def __init__(self, **data):
        assets_dir = Path(__file__).parent.parent / "assets"
        super().__init__(
            name="キャラクター名",
            nickname="愛称",
            attributes=["属性1", "属性2"],
            personality="性格の説明",
            speech_style=SpeechStyle(
                tone="話し方のトーン",
                patterns=["～だよ", "～ね"],
                examples=["例文1", "例文2"],
                forbidden=["禁止事項1", "禁止事項2"],
            ),
            portrait=assets_dir / "my_portrait.png",
            full_body=assets_dir / "my_fullbody.png",
            **data,
        )
```

### 2. コードから使用

```python
from manganize.agents import ManganizeAgent
from manganize.character import MyCharacter

character = MyCharacter()
agent = ManganizeAgent(character=character)
graph = agent.compile_graph()

# マンガ生成
result = graph.invoke({"topic": "技術トピック"})
```

## キャラクター設定のポイント

### attributes（属性）

キャラクターの属性をリストで指定します。複数の属性を設定でき、プロンプト内では「 / 」で結合されて表示されます。例：

- `["ハイスキルエンジニア", "技術オタク"]` → "ハイスキルエンジニア / 技術オタク"
- `["天才ハッカー", "セキュリティ専門家", "倫理的ハッカー"]` → "天才ハッカー / セキュリティ専門家 / 倫理的ハッカー"

属性はキャラクターの専門性や特徴を端的に表現するキーワードを設定してください。

### speech_style.tone（話し方のトーン）

キャラクターの基本的な話し方を説明します。例：

- "明るく元気な話し方"
- "落ち着いた大人の女性"
- "少年のような元気な口調"

### speech_style.patterns（語尾パターン）

キャラクターがよく使う語尾のリストです。例：

- カジュアル: "～だよ", "～ね", "～かな"
- クール: "～かも", "～だね", "……"
- 元気: "～だよ！", "～ね！", "～です！"

### speech_style.forbidden（禁止事項）

キャラクターに使わせたくない口調や表現を指定します。例：

- "堅苦しい敬語"
- "おじさん構文"
- "古風な言い回し（～じゃ、～わい）"

### personality（性格）

キャラクターの性格や振る舞いを説明します。この情報は：

- シナリオライターがセリフを考える際の参考になります
- 画像生成AIが表情や仕草を決める際に使用されます

## サンプルキャラクター

デフォルトの「くらげちゃん」の設定は `characters/kurage.yaml` にあります。これを参考にして独自のキャラクターを作成してください。

## トラブルシューティング

### 画像が読み込めない

- 画像ファイルのパスが正しいか確認してください
- YAMLファイルからの相対パスで指定されているか確認してください
- 画像ファイルが PNG 形式であることを確認してください

### キャラクターが反映されない

- YAMLファイルの構文が正しいか確認してください（インデントに注意）
- `--character` オプションで正しいパスを指定しているか確認してください

### セリフの口調がおかしい

- `speech_style.patterns` と `speech_style.forbidden` を調整してください
- `speech_style.tone` の説明をより具体的にしてください
- `speech_style.examples` にセリフの例を追加してください

## 関連ドキュメント

- [キャラクターモデルのリファレンス](../reference/character-model.md)
- [プロンプトテンプレートの仕組み](../explanation/prompt-templates.md)
