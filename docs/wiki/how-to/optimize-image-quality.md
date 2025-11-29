# 画像品質を最適化する

このガイドでは、生成される漫画画像の品質を向上させる方法を説明します。

## 目的

- 画像生成パラメータを理解する
- 高品質な画像を生成する設定を学ぶ
- 画像サイズと品質のトレードオフを理解する

## 画像生成パラメータ

Manganize では、Gemini 3 Pro Image Preview モデルの `ImageConfig` を使って画像を生成します。

```python
config=types.GenerateContentConfig(
    image_config=types.ImageConfig(
        aspect_ratio="9:16",  # アスペクト比
        image_size="2K"       # 画像サイズ
    ),
    ...
)
```

## 方法 1: アスペクト比を変更する

### 利用可能なアスペクト比

| アスペクト比 | 用途 | 解像度（2K の場合） |
|-------------|------|-------------------|
| `"1:1"` | 正方形（SNS 投稿向け） | 2048×2048 |
| `"3:4"` | 縦長（雑誌サイズ） | 1536×2048 |
| `"4:3"` | 横長（プレゼン向け） | 2048×1536 |
| `"9:16"` | 縦長（スマホ向け） | 1152×2048 |
| `"16:9"` | 横長（PC/TV 向け） | 2048×1152 |

### 実装例

`tools.py` を編集して、アスペクト比をパラメータ化します。

```python
@tool
def generate_manga_image(
    content: str,
    aspect_ratio: str = "9:16",
    runtime: ToolRuntime,
) -> Command:
    """漫画風の画像を生成するツール。

    Args:
        content: 画像生成のためのコンテンツ
        aspect_ratio: アスペクト比（"1:1", "3:4", "4:3", "9:16", "16:9"）
    """
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[...],
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,  # パラメータを使用
                image_size="2K",
            ),
            tools=[{"google_search": {}}],
        ),
    )
    ...
```

## 方法 2: 画像サイズを変更する

### 利用可能な画像サイズ

| サイズ | 説明 | 長辺のピクセル数 | 用途 |
|-------|------|----------------|------|
| `"1K"` | 低解像度 | 約 1024px | プレビュー、高速生成 |
| `"2K"` | 標準解像度 | 約 2048px | 一般的な用途 |
| `"4K"` | 高解像度 | 約 4096px | 印刷、高品質出力 |

### トレードオフ

| 項目 | 1K | 2K | 4K |
|------|----|----|-----|
| 生成速度 | 速い | 普通 | 遅い |
| API コスト | 低い | 普通 | 高い |
| 画質 | 低い | 普通 | 高い |
| ファイルサイズ | 小さい | 普通 | 大きい |

### 実装例

```python
@tool
def generate_manga_image(
    content: str,
    aspect_ratio: str = "9:16",
    image_size: str = "2K",
    runtime: ToolRuntime,
) -> Command:
    """漫画風の画像を生成するツール。

    Args:
        content: 画像生成のためのコンテンツ
        aspect_ratio: アスペクト比
        image_size: 画像サイズ（"1K", "2K", "4K"）
    """
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[...],
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size,  # パラメータを使用
            ),
            tools=[{"google_search": {}}],
        ),
    )
    ...
```

## 方法 3: プロンプトで画質を向上させる

### 画質に関するプロンプト技法

```python
MANGANIZE_AGENT_SYSTEM_PROMPT = """
# Art Style & Layout
- スタイル：「まんがタイムきらら」風のアートスタイル。
    - 特徴：
      * 太すぎない柔らかな主線
      * パステル調または鮮やかな彩色
      * 大きな目、かわいいデフォルメ
      * 高品質で滑らかな線画 ← 追加
      * 背景も丁寧に描画 ← 追加
      * アンチエイリアスをかけた綺麗な仕上がり ← 追加

# Quality Requirements ← 新しいセクション
- 画像は高品質で、細部まで丁寧に描画すること
- 線画は滑らかで、ジャギーがないこと
- 色彩は鮮やかで、グラデーションも美しいこと
- キャラクターの表情は豊かで、感情が伝わること
"""
```

### 詳細度を上げる

```python
MANGANIZE_AGENT_SYSTEM_PROMPT = """
...

# Content / Story
以下のコンテンツを元に、起承転結のあるストーリー構成にしてください。
各コマは以下の要素を含むこと： ← 追加
- 明確なキャラクターの表情と動き
- 背景やディテールの描画
- 適切なカメラアングル（アップ、ロング、俯瞰など）
- 効果線や集中線などの漫画的表現

コンテンツ:
{content}
"""
```

## 方法 4: 参照画像の品質を向上させる

### キャラクター参照画像の要件

良い参照画像の条件：

- **解像度**: 最低 512×512px、推奨 1024×1024px 以上
- **背景**: 単色またはシンプルな背景
- **構図**: キャラクターが中心に配置
- **品質**: 鮮明で、ぼやけていないこと
- **形式**: PNG（透過背景が理想）

### 参照画像の前処理

```python
from PIL import Image, ImageEnhance

def enhance_reference_image(image_path: Path) -> bytes:
    """参照画像を高品質化する。"""
    image = Image.open(image_path)

    # リサイズ（アップスケール）
    if image.width < 1024:
        new_size = (1024, int(1024 * image.height / image.width))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # シャープネスを向上
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)

    # コントラストを調整
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)

    # バイト列に変換
    from io import BytesIO
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
```

`tools.py` で使用する：

```python
def load_kurage_image() -> bytes:
    image_path = Path(__file__).parent.parent / "assets" / "kurage.png"
    return enhance_reference_image(image_path)  # 前処理を追加
```

## 方法 5: 後処理で画質を向上させる

### AI アップスケーリング

生成された画像を AI でアップスケーリングします。

```python
from PIL import Image
from io import BytesIO

def upscale_image(image_data: bytes, scale: int = 2) -> bytes:
    """画像をアップスケーリングする。

    Args:
        image_data: 画像データ
        scale: スケール倍率（2, 4, 8）

    Returns:
        アップスケーリングされた画像データ
    """
    image = Image.open(BytesIO(image_data))

    # 単純なリサイズ（実際には Real-ESRGAN などの AI を使用推奨）
    new_size = (image.width * scale, image.height * scale)
    upscaled = image.resize(new_size, Image.Resampling.LANCZOS)

    buffer = BytesIO()
    upscaled.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
```

### シャープネス調整

```python
from PIL import ImageEnhance, ImageFilter

def enhance_manga_image(image_data: bytes) -> bytes:
    """漫画画像を後処理で高品質化する。"""
    image = Image.open(BytesIO(image_data))

    # アンシャープマスク適用
    image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    # シャープネス向上
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.3)

    # コントラスト調整
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.1)

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
```

`main.py` で使用する：

```python
result = agent(
    "次のコンテンツをマンガにしてください: ...",
    thread_id="1",
)

if result.get("generated_image"):
    # 後処理を適用
    enhanced_image_data = enhance_manga_image(result["generated_image"])

    image = Image.open(BytesIO(enhanced_image_data))
    image.save("enhanced_manga.png")
```

## 推奨設定

### 用途別の推奨設定

#### SNS 投稿用

```python
aspect_ratio = "1:1"  # 正方形
image_size = "2K"     # 標準解像度
```

#### スマホ閲覧用

```python
aspect_ratio = "9:16"  # 縦長
image_size = "2K"      # 標準解像度
```

#### 印刷用

```python
aspect_ratio = "3:4"  # 雑誌サイズ
image_size = "4K"     # 高解像度
```

#### プレビュー/テスト用

```python
aspect_ratio = "16:9"  # 横長
image_size = "1K"      # 低解像度（高速）
```

## トラブルシューティング

### 画像がぼやけている

- 画像サイズを `"4K"` に上げる
- プロンプトに「高品質」「鮮明」などのキーワードを追加
- 参照画像の解像度を確認

### 生成に時間がかかりすぎる

- 画像サイズを `"1K"` または `"2K"` に下げる
- プロンプトを簡潔にする

### ファイルサイズが大きすぎる

- 後処理で PNG を最適化
- JPEG に変換（ただし品質は低下）

```python
image.save("manga.jpg", format="JPEG", quality=85, optimize=True)
```

## まとめ

このガイドでは、以下を学びました。

- 画像生成パラメータ（アスペクト比、画像サイズ）の調整方法
- プロンプトによる画質向上技法
- 参照画像と後処理による品質改善
- 用途別の推奨設定

## 関連ドキュメント

- [API リファレンス - ImageConfig](../reference/api.md#imageconfig) - 画像設定の詳細
- [プロンプトをカスタマイズする](customize-prompt.md) - プロンプト技法の詳細

