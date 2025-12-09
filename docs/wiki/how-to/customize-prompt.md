# プロンプトをカスタマイズする

## プロンプトの構成

`manganize/prompts.py` に 3 つのプロンプトが定義されています：

| プロンプト | 役割 |
|------------|------|
| `MANGANIZE_RESEARCHER_SYSTEM_PROMPT` | 情報収集・構造化 |
| `MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT` | 脚本作成 |
| `MANGANIZE_IMAGE_GENERATION_SYSTEM_PROMPT` | 画像生成 |

## Researcher プロンプトのカスタマイズ

情報収集の方法や出力形式を変更：

```python
MANGANIZE_RESEARCHER_SYSTEM_PROMPT = """
あなたは、技術解説マンガのために情報を整理する構成作家AIです。

## 出力フォーマット
# トピック名: [技術名]
# 推奨コマ数: [4コマ]

## 1. 技術的要点（3点要約）
* [要点1]
...
"""
```

## Scenario Writer プロンプトのカスタマイズ

キャラクター設定や口調を変更：

```python
MANGANIZE_SCENARIO_WRITER_SYSTEM_PROMPT = """
## 担当キャラクター
* **名前:** くらがりくらげ（愛称：くらげちゃん）
* **口調:** 「～かも」「～だね」といったニュートラルで気だるげな語尾

## 出力フォーマット
**【1コマ目】**
* **状況:** [導入]
* **視覚的指示:** [作画指示]
* **セリフ:** くらげ: 「...」
...
"""
```

## Image Generation プロンプトのカスタマイズ

画風やレイアウトを変更：

```python
MANGANIZE_IMAGE_GENERATION_SYSTEM_PROMPT = """
# Role
あなたは「まんがタイムきらら」系列の画風で漫画を生成するプロの漫画家です。

# Art Style & Props
- スタイル：「まんがタイムきらら」風
- 特徴：太すぎない柔らかな主線、鮮やかながらも目に優しい彩色

# Layout & Composition
- 構成：縦に並んだ4コマ漫画
- 吹き出し：読みやすい配置、日本語セリフ
"""
```

## キャラクター画像の変更

1. 新しい画像を `assets/` に配置
2. `tools.py` の `load_kurage_image` / `load_kurage_full_image` を修正

```python
def load_kurage_image() -> bytes:
    image_path = Path(__file__).parent.parent / "assets" / "new_character.png"
    return image_path.read_bytes()
```

## 変更の適用

```bash
# キャッシュをクリアして再実行
find . -type d -name __pycache__ -exec rm -rf {} +
uv run python main.py "テスト"
```
