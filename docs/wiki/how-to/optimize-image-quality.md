# 画像品質を最適化する

## 画像生成パラメータ

`tools.py` の `generate_manga_image` で設定：

```python
config=types.GenerateContentConfig(
    image_config=types.ImageConfig(
        aspect_ratio="9:16",
        image_size="2K"
    ),
)
```

## アスペクト比

| 値 | 用途 | 解像度（2K） |
|----|------|-------------|
| `"1:1"` | SNS 投稿 | 2048×2048 |
| `"3:4"` | 雑誌サイズ | 1536×2048 |
| `"9:16"` | スマホ向け | 1152×2048 |
| `"16:9"` | PC/TV 向け | 2048×1152 |

## 画像サイズ

| サイズ | 長辺 | 用途 |
|--------|------|------|
| `"1K"` | 約 1024px | プレビュー、高速生成 |
| `"2K"` | 約 2048px | 一般的な用途 |
| `"4K"` | 約 4096px | 印刷、高品質出力 |

トレードオフ：サイズを上げると生成速度低下、コスト増加。

## 用途別推奨設定

### SNS 投稿

```python
aspect_ratio = "1:1"
image_size = "2K"
```

### スマホ閲覧

```python
aspect_ratio = "9:16"
image_size = "2K"
```

### 印刷

```python
aspect_ratio = "3:4"
image_size = "4K"
```

## プロンプトで品質向上

`prompts.py` の Image Generation プロンプトに追加：

```
# Quality Requirements
- 画像は高品質で、細部まで丁寧に描画
- 線画は滑らかで、ジャギーがない
- キャラクターの表情は豊かで、感情が伝わる
```

## 参照画像の品質

推奨条件：
- 解像度: 1024×1024px 以上
- 背景: シンプル（単色または透過）
- 構図: キャラクターが中心
- 形式: PNG

## 後処理

```python
from PIL import Image, ImageEnhance, ImageFilter

def enhance_image(image_data: bytes) -> bytes:
    image = Image.open(BytesIO(image_data))

    # アンシャープマスク
    image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150))

    # シャープネス向上
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.3)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
```

## トラブルシューティング

### 画像がぼやけている
- `image_size` を `"4K"` に変更
- プロンプトに「高品質」を追加

### 生成が遅い
- `image_size` を `"1K"` または `"2K"` に変更

### ファイルサイズが大きい
- JPEG に変換（品質 85%）
```python
image.save("manga.jpg", format="JPEG", quality=85)
```
