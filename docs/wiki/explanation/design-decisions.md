# 設計の意思決定

このドキュメントは、Manganize の設計において行われた主要な意思決定とその背景を説明します。

## 1. LangGraph の採用

### 決定内容

LangGraph をエージェントフレームワークとして採用しました。

### 背景と理由

**検討した選択肢**:

1. **LangChain のみ**: シンプルなチェーンで実装
2. **LangGraph**: 状態管理とグラフベースのフロー
3. **独自実装**: スクラッチでエージェントを実装

**採用理由**:

- **状態管理の明確性**: `AgentState` で状態を型安全に管理できる
- **チェックポイント機能**: 会話履歴の保存・復元が簡単
- **拡張性**: 複雑なワークフローにも対応できる
- **エコシステム**: LangChain との統合が容易

**トレードオフ**:

- **学習コスト**: LangChain と LangGraph の両方を理解する必要がある
- **抽象化のオーバーヘッド**: シンプルなケースでは過剰に感じる可能性

**代替案との比較**:

| 項目 | LangChain のみ | LangGraph | 独自実装 |
|------|---------------|-----------|----------|
| 状態管理 | △ | ◎ | ○ |
| 学習コスト | ○ | △ | ◎（設計次第） |
| 拡張性 | △ | ◎ | ○ |
| メンテナンス | ○ | ○ | △ |

### 参考資料

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Why LangGraph?](https://blog.langchain.dev/langgraph-multi-agent-workflows/)

## 2. Gemini 3 Pro Image Preview の選択

### 決定内容

画像生成モデルとして Gemini 3 Pro Image Preview を採用しました。

### 背景と理由

**検討した選択肢**:

1. **Gemini 3 Pro Image Preview**: Google の最新画像生成モデル
2. **DALL-E 3**: OpenAI の画像生成モデル
3. **Stable Diffusion**: オープンソースの画像生成モデル
4. **Midjourney**: 高品質な画像生成サービス

**採用理由**:

- **マルチモーダル**: テキストと画像の両方を入力できる
- **スタイル制御**: プロンプトで詳細なスタイル指定が可能
- **Google Search 連携**: リアルタイムの情報取得が可能
- **API の利便性**: LangChain との統合が容易
- **コスト効率**: 比較的低コストで利用可能

**トレードオフ**:

- **モデルの制限**: Google のポリシーに依存
- **API の安定性**: プレビュー版のため、変更の可能性がある

**代替案との比較**:

| 項目 | Gemini 3 | DALL-E 3 | Stable Diffusion | Midjourney |
|------|----------|----------|------------------|------------|
| マルチモーダル | ◎ | △ | × | × |
| スタイル制御 | ◎ | ○ | ◎ | ◎ |
| API 利用 | ◎ | ◎ | ○ | △ |
| コスト | ○ | △ | ◎ | △ |
| 品質 | ◎ | ◎ | ○ | ◎ |

### 参考資料

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Image Generation with Gemini](https://ai.google.dev/gemini-api/docs/image-generation)

## 3. プロンプト設計

### 決定内容

構造化されたプロンプトテンプレートを採用しました。

```
# Role
# Character Reference
# Art Style & Layout
# Negative Constraints
# Content / Story
```

### 背景と理由

**検討した選択肢**:

1. **シンプルなプロンプト**: 1-2 行の簡単な指示
2. **構造化プロンプト**: セクションごとに整理（採用）
3. **Few-shot プロンプト**: 例を複数提示

**採用理由**:

- **明確性**: 各セクションの役割が明確
- **メンテナンス性**: セクションごとに編集しやすい
- **拡張性**: 新しいセクションを追加しやすい
- **一貫性**: 出力の品質が安定する

**プロンプトエンジニアリングの原則**:

1. **具体性**: 「良い感じに」ではなく「太すぎない柔らかな主線」
2. **制約の明示**: 「〜しないこと」を明確に記述
3. **例の提供**: キャラクター画像を添付
4. **構造化**: セクションごとに整理

**プロンプトの進化**:

```
バージョン 1（初期）:
"マンガを描いてください"

バージョン 2（改善）:
"4コママンガを描いてください。キャラクターはかわいく描いてください。"

バージョン 3（現在）:
構造化されたプロンプト（Role, Character, Style, Constraints）
```

### 参考資料

- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Best Practices for Prompt Engineering](https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api)

## 4. 型ヒントの徹底

### 決定内容

すべての関数に型ヒントを付与し、mypy で静的型チェックを実施します。

### 背景と理由

**採用理由**:

- **バグの早期発見**: 実行前に型エラーを検出
- **ドキュメント効果**: 型がドキュメントの役割を果たす
- **IDE サポート**: 補完やリファクタリングが正確になる
- **保守性**: コードの意図が明確になる

**例**:

```python
# Good
def generate_manga_image(
    content: str,
    runtime: ToolRuntime,
) -> Command:
    ...

# Bad
def generate_manga_image(content, runtime):
    ...
```

**厳格性のレベル**:

mypy の設定で厳格な型チェックを有効化しています。

```toml
[tool.mypy]
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

**トレードオフ**:

- **初期コスト**: 型ヒントの記述に時間がかかる
- **学習コスト**: Python の型システムを理解する必要がある

**効果**:

- 型エラーを実行前に検出できた例: 10+ 件
- リファクタリングが安全に実行できた: 複数回

## 5. uv によるパッケージ管理

### 決定内容

パッケージマネージャーとして `uv` を採用しました。

### 背景と理由

**検討した選択肢**:

1. **pip + requirements.txt**: 従来の方法
2. **Poetry**: 人気の Python パッケージマネージャー
3. **uv**: 高速な Python パッケージマネージャー（採用）

**採用理由**:

- **高速**: Rust 実装による高速なパッケージ解決とインストール
- **シンプル**: 最小限の設定ファイル（pyproject.toml）
- **互換性**: pip や Poetry から移行しやすい
- **依存関係の管理**: lockfile による再現可能なビルド

**ベンチマーク（参考）**:

| ツール | インストール時間 |
|--------|----------------|
| pip | 30 秒 |
| Poetry | 25 秒 |
| uv | 5 秒 |

**トレードオフ**:

- **新しいツール**: 情報やコミュニティが Poetry より少ない
- **安定性**: まだ発展途上のツール

**代替案との比較**:

| 項目 | pip | Poetry | uv |
|------|-----|--------|-----|
| 速度 | △ | ○ | ◎ |
| 依存関係解決 | △ | ◎ | ◎ |
| lockfile | × | ◎ | ◎ |
| 学習コスト | ○ | △ | ○ |

### 参考資料

- [uv Documentation](https://github.com/astral-sh/uv)

## 6. チェックポインターの選択

### 決定内容

初期実装では `InMemorySaver` を使用します。

### 背景と理由

**検討した選択肢**:

1. **InMemorySaver**: メモリベース（採用）
2. **PostgresSaver**: PostgreSQL ベース
3. **RedisSaver**: Redis ベース
4. **FileSaver**: ファイルベース

**現在の採用理由**:

- **シンプル性**: 追加の依存関係が不要
- **開発速度**: セットアップが不要
- **テスト容易性**: 状態のクリアが簡単

**トレードオフ**:

- **永続化なし**: サーバー再起動で履歴が失われる
- **スケール制限**: 複数プロセスで状態を共有できない

**本番環境での推奨**:

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver(
    connection_string=os.getenv("DATABASE_URL")
)
```

**段階的な移行戦略**:

```
Phase 1: InMemorySaver（現在）
  ↓ 開発・テストで十分動作

Phase 2: PostgresSaver
  ↓ 本番環境で永続化が必要に

Phase 3: Redis + PostgreSQL
  ↓ 高頻度アクセスはキャッシュ、履歴は DB
```

## 7. ディレクトリ構造

### 決定内容

フラットで最小限のディレクトリ構造を採用しました。

```
manganize/
├── manganize/       # メインパッケージ
│   ├── chain.py
│   ├── tools.py
│   └── prompts.py
├── main.py          # エントリーポイント
├── assets/          # 静的ファイル
└── docs/            # ドキュメント
```

### 背景と理由

**採用理由**:

- **シンプル性**: 小規模プロジェクトに適している
- **ナビゲーション**: ファイルが見つけやすい
- **学習コスト**: 新規参加者が理解しやすい

**代替案**:

より複雑な構造（将来の拡張を見据えた場合）:

```
manganize/
├── manganize/
│   ├── agents/      # エージェント層
│   ├── tools/       # ツール層
│   ├── prompts/     # プロンプト層
│   ├── models/      # データモデル
│   └── utils/       # ユーティリティ
```

**移行戦略**:

プロジェクトが成長したら、段階的にリファクタリングします。

```
ファイル数 < 10: フラット構造（現在）
ファイル数 10-30: モジュールごとに分離
ファイル数 > 30: 階層的な構造
```

## 8. エラーハンドリング戦略

### 決定内容

ツール内で例外をキャッチし、`Command` オブジェクトでエラーを返します。

```python
if image_parts:
    # 成功
    return Command(update={"generated_image": image_data, ...})

# 失敗
return Command(update={"generated_image": None, ...})
```

### 背景と理由

**採用理由**:

- **エージェントの継続**: 例外で停止せず、エージェントがエラーから回復できる
- **ログの一貫性**: エラーもメッセージ履歴に記録される
- **ユーザー体験**: エラーが適切に伝わる

**代替案**:

例外を伝播させる方法:

```python
def generate_manga_image(content: str) -> bytes:
    # エラー時に例外を投げる
    if not image_parts:
        raise ImageGenerationError("画像生成に失敗しました")

    return image_data
```

**採用しなかった理由**:

- エージェントが停止してしまう
- ユーザーに分かりにくいエラーメッセージが表示される

## 9. テスト戦略

### 決定内容

初期段階では手動テストを中心に、将来的にユニットテストと統合テストを追加します。

### 背景と理由

**現在のアプローチ**:

- 手動テスト: `main.py` を実行して動作確認
- 型チェック: mypy による静的型チェック
- リント: ruff によるコード品質チェック

**将来の計画**:

```python
# tests/test_tools.py
def test_generate_manga_image():
    # モックを使用
    with patch("manganize.tools.genai.Client") as mock_client:
        ...
        result = generate_manga_image.invoke({"content": "test"})
        assert result is not None
```

**段階的なアプローチ**:

```
Phase 1: 手動テスト + 型チェック（現在）
  ↓
Phase 2: ユニットテスト追加
  ↓
Phase 3: 統合テスト追加
  ↓
Phase 4: E2E テスト追加
```

**理由**:

- 初期段階では機能の実装を優先
- テストの投資対効果を考慮
- 型チェックで基本的な品質を担保

## まとめ

これらの設計決定は、以下の原則に基づいています。

1. **シンプルさ優先**: 必要最小限から始める
2. **段階的な改善**: 必要に応じて拡張する
3. **型安全性**: 型チェックでバグを防ぐ
4. **保守性**: 将来のメンテナンスを考慮
5. **学習コスト**: 新規参加者が理解しやすい

## 関連ドキュメント

- [アーキテクチャ解説](architecture.md) - システム全体の構造
- [API リファレンス](../reference/api.md) - API の詳細仕様
- [LangGraph を理解する](../tutorials/understanding-langgraph.md) - LangGraph の基礎

