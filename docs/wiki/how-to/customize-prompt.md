# プロンプトをカスタマイズする

このガイドでは、Manganize のプロンプトをカスタマイズして、異なるスタイルの漫画を生成する方法を説明します。

## 目的

- プロンプトの構造を理解する
- 独自のキャラクターやスタイルを適用する
- プロンプトのベストプラクティスを学ぶ

## プロンプトの構造

現在のプロンプトは `manganize/prompts.py` に定義されています。

```python
MANGANIZE_AGENT_SYSTEM_PROMPT = """
# Role
あなたは「まんがタイムきらら」系列で連載を持っている、萌え系日常4コマ漫画のプロ作家です。
...

# Character Reference
添付画像のキャラクターを主役として描いてください。
...

# Art Style & Layout
- スタイル：「まんがタイムきらら」風のアートスタイル。
...

# Negative Constraints
- 既存の雑誌名やコミックスのロゴを画像内に含めないこと。
...

# Content / Story
以下のコンテンツを元に、起承転結のあるストーリー構成にしてください：
{content}
"""
```

## 方法 1: スタイルを変更する

### 少年漫画風に変更する

```python
MANGANIZE_AGENT_SYSTEM_PROMPT = """
# Role
あなたは週刊少年ジャンプで連載を持っている、バトル漫画のプロ作家です。
熱血・友情・勝利をテーマにした、迫力のある漫画を生成してください。

# Character Reference
添付画像のキャラクターを主人公として描いてください。
- 名前：くらがりくらげ
- 外見的特徴は添付画像を参照すること。
- 熱血で正義感が強い性格として描いてください。

# Art Style & Layout
- スタイル：週刊少年ジャンプ風のアートスタイル。
    - 特徴：力強い主線、コントラストの強い影、迫力のある構図。
- 構成：見開き2ページの漫画形式（6-8コマ）。
- 吹き出し：読みやすい配置にし、セリフは「日本語」で記述すること。
- 効果音：擬音語を積極的に使用すること。

# Content / Story
以下のコンテンツを元に、起承転結のあるストーリー構成にしてください：
{content}
"""
```

### 変更を適用する

`manganize/prompts.py` を編集して、上記のプロンプトに置き換えます。

```bash
# エディタで編集
vim manganize/prompts.py

# または、全体を置き換えたい場合
cat > manganize/prompts.py << 'EOF'
MANGANIZE_AGENT_SYSTEM_PROMPT = """
# ここに新しいプロンプトを記述
"""
EOF
```

## 方法 2: 複数のプロンプトを切り替える

複数のスタイルを使い分けたい場合は、プロンプトを辞書で管理します。

```python
# prompts.py

MANGA_STYLES = {
    "kirara": """
    # Role
    あなたは「まんがタイムきらら」系列で連載を持っている...
    """,

    "shonen": """
    # Role
    あなたは週刊少年ジャンプで連載を持っている...
    """,

    "seinen": """
    # Role
    あなたは青年漫画誌で連載を持っている...
    """,
}

def get_prompt(style: str = "kirara") -> str:
    """指定されたスタイルのプロンプトを取得する。"""
    return MANGA_STYLES.get(style, MANGA_STYLES["kirara"])
```

### エージェントで使用する

```python
# chain.py

from manganize.prompts import get_prompt

class ManganizeAgent:
    def __init__(self, model: BaseChatModel | None = None, style: str = "kirara"):
        self.style = style
        self.agent = create_agent(
            model=model or init_chat_model(model="google_genai:gemini-2.5-flash"),
            tools=[generate_manga_image],
            state_schema=ManganizeAgentState,
            system_prompt=SystemMessage(content=get_prompt(style)),
            checkpointer=InMemorySaver(),
        )
```

```python
# main.py

# きららスタイルで生成
agent_kirara = ManganizeAgent(style="kirara")

# 少年漫画スタイルで生成
agent_shonen = ManganizeAgent(style="shonen")
```

## 方法 3: キャラクターを変更する

### 新しいキャラクター画像を追加する

1. キャラクター画像を `assets/` フォルダに配置します。

```bash
cp /path/to/new-character.png assets/new-character.png
```

2. `tools.py` の `load_kurage_image` 関数を修正します。

```python
def load_character_image(character: str = "kurage") -> bytes:
    """キャラクター画像を読み込む。"""
    image_path = Path(__file__).parent.parent / "assets" / f"{character}.png"
    if not image_path.exists():
        # デフォルトのキャラクターを返す
        image_path = Path(__file__).parent.parent / "assets" / "kurage.png"
    return image_path.read_bytes()
```

3. `generate_manga_image` 関数を修正します。

```python
@tool
def generate_manga_image(content: str, character: str = "kurage", runtime: ToolRuntime) -> Command:
    """漫画風の画像を生成するツール。

    Args:
        content: 画像生成のためのコンテンツ
        character: 使用するキャラクター名（デフォルト: "kurage"）
    """
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[
            types.Part.from_text(
                text=MANGANIZE_AGENT_SYSTEM_PROMPT.format(content=content)
            ),
            types.Part.from_bytes(
                data=load_character_image(character),  # キャラクター指定
                mime_type="image/png",
            ),
        ],
        ...
    )
    ...
```

## 方法 4: プロンプトエンジニアリングのベストプラクティス

### 明確な役割を定義する

```python
# Good
"""
# Role
あなたは20年のキャリアを持つプロの4コマ漫画家です。
読者に笑いと癒しを提供することを使命としています。
"""

# Bad
"""
漫画を描いてください。
"""
```

### 具体的な制約を設定する

```python
# Good
"""
# Constraints
- コマ数は4コマ固定とすること
- セリフは1コマあたり最大20文字とすること
- 背景は簡略化し、キャラクターに焦点を当てること
"""

# Bad
"""
いい感じに描いてください。
"""
```

### ネガティブプロンプトを活用する

```python
"""
# Negative Constraints
- 既存の雑誌名やロゴを含めないこと
- 暴力的・性的な表現を避けること
- キャラクターの特徴を勝手に変更しないこと
"""
```

## トラブルシューティング

### プロンプトを変更したのに反映されない

Python のモジュールがキャッシュされている可能性があります。以下を試してください。

```bash
# キャッシュをクリア
find . -type d -name __pycache__ -exec rm -rf {} +

# 再実行
uv run python main.py
```

### 生成される画像が意図と異なる

プロンプトが曖昧な可能性があります。以下を確認してください。

- 役割が明確に定義されているか
- スタイルの特徴が具体的に記述されているか
- ネガティブ制約が適切に設定されているか

### キャラクターが認識されない

参照画像の品質を確認してください。

- 画像が鮮明であること
- キャラクターが中心に配置されていること
- 背景がシンプルであること

## まとめ

このガイドでは、以下の方法を学びました。

- プロンプトの構造とカスタマイズ方法
- 複数のスタイルを切り替える方法
- キャラクター画像を変更する方法
- プロンプトエンジニアリングのベストプラクティス

## 関連ドキュメント

- [API リファレンス](../reference/api.md) - プロンプト関連の API 仕様
- [アーキテクチャの理解](../explanation/architecture.md) - プロンプトがどのように処理されるか

