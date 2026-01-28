# AGENTS.md - コーディングエージェント向けガイド

このドキュメントは、AI コーディングエージェントがこのプロジェクトで作業する際の方針とルールを定義します。

**重要**: このガイドは、プロジェクトの憲章（[Constitution](.specify/memory/constitution.md)）に基づいています。憲章は根本的な原則を定義し、このガイドは実行時の具体的な手順を提供します。両者は補完的な関係にあります。

## プロジェクト概要

**manganize** は、テキストコンテンツをマンガ画像に変換する LangGraph ベースの AI エージェントです。

### 技術スタック

#### コアエージェント
- **言語**: Python 3.13+
- **パッケージ管理**: uv
- **フレームワーク**: LangGraph / LangChain
- **LLM**: Google Generative AI (Gemini)
- **開発ツール**: ty（型チェック）, ruff（リント・フォーマット）

#### Webアプリケーション
- **Web フレームワーク**: FastAPI
- **テンプレートエンジン**: Jinja2
- **フロントエンド動的化**: HTMX
- **スタイリング**: TailwindCSS
- **リアルタイム通信**: SSE（Server-Sent Events）

## Spec 駆動開発

このプロジェクトでは、仕様と実装の同期を保つために **Spec 駆動開発** を採用しています。

### Spec ファイルの配置

```
docs/specs/
├── core-agent/           # エージェント本体の仕様
├── image-generation/     # マンガ画像生成機能の仕様
└── shared/               # 共通仕様（複数機能で共有）
```

### 各機能ディレクトリの構成

| ファイル | 説明 |
|----------|------|
| `requirements.md` | EARS 記法での要件定義 |
| `design.md` | 実装方針・アーキテクチャ設計 |
| `tasks.md` | 実装タスク一覧（チェックリスト形式） |

### EARS 記法について

requirements.md では以下の EARS（Easy Approach to Requirements Syntax）パターンを使用します：

- **Ubiquitous**: 「システムは〜すること」（常に成り立つ要件）
- **Event-driven**: 「〜の場合、システムは〜すること」（イベント駆動の要件）
- **State-driven**: 「〜の状態のとき、システムは〜すること」（状態依存の要件）
- **Optional**: 「ユーザーが〜を選択した場合、システムは〜すること」（オプション機能）

## 開発ワークフロー

### 基本フロー（Spec → 実装）

1. **要件定義**: `requirements.md` で要件を定義または更新
2. **設計更新**: `design.md` で実装方針を設計
3. **タスク生成**: `tasks.md` でタスクを生成または更新
4. **実装**: タスクに沿ってコードを実装

### 逆フロー（実装 → Spec）

探索的な実装や試行錯誤の後に仕様を固める場合：

1. 実装を行う
2. 「この変更を Spec に反映して」と依頼
3. 適切な Spec ファイルを更新

## フロントエンド開発

### TailwindCSS のワークフロー

**重要**: このプロジェクトは TailwindCSS 4.x を使用しています（`@import "tailwindcss";` 構文）。

1. **初回セットアップ**: `npm install`
2. **スタイルの編集**: `apps/web/manganize_web/static/css/input.css` でカスタムスタイルを定義
3. **watch モード起動**: `npx @tailwindcss/cli -i apps/web/manganize_web/static/css/input.css -o apps/web/manganize_web/static/css/output.css --watch`
4. **ビルド確認**: `apps/web/manganize_web/static/css/output.css` が自動更新されることを確認
5. **本番ビルド**: `npx @tailwindcss/cli -i apps/web/manganize_web/static/css/input.css -o apps/web/manganize_web/static/css/output.css --minify`

### HTMX の使い方

- **動的更新**: `hx-get`, `hx-post` でサーバーサイドレンダリングされた HTML を部分更新
- **プログレスバー**: `hx-indicator` でローディングインジケーターを表示
- **無限スクロール**: `hx-trigger="revealed"` でスクロール時の自動読み込み
- **フォーム送信**: `hx-post` でフォームを非同期送信

### Alpine.js の使い方

- **モーダル**: `x-data`, `x-show` でモーダルダイアログを実装
- **状態管理**: `x-data` で軽量な状態管理
- **イベントハンドリング**: `@click`, `@submit` でクライアントサイドのインタラクション

### SSE（Server-Sent Events）

- **進捗通知**: `EventSource` API でリアルタイム進捗更新
- **再接続**: 自動再接続ロジックとエラーハンドリング
- **実装場所**: `apps/web/manganize_web/templates/partials/progress.html`

## コーディング規約

### 型ヒント

- すべての関数に型ヒントを付与すること
- `ty` でエラーが出ないことを確認

```python
# Good
def process_text(text: str) -> dict[str, Any]:
    ...

# Bad
def process_text(text):
    ...
```

### フォーマット・リント

- `ruff` でフォーマットとリントを実行
- 警告がある場合は修正してからコミット

### コミットメッセージ

Angular Convention に従う：

| プレフィックス | 用途 |
|---------------|------|
| `feat:` | 新機能 |
| `fix:` | バグ修正 |
| `docs:` | ドキュメントのみの変更 |
| `style:` | コードの意味に影響しない変更（フォーマット等） |
| `refactor:` | バグ修正でも機能追加でもないコード変更 |
| `perf:` | パフォーマンス改善 |
| `test:` | テストの追加・修正 |
| `chore:` | ビルドプロセスや補助ツールの変更 |

例: `feat: add manga panel layout options`

## エージェントへの指示

### 実装前

1. 関連する `docs/specs/` 内の Spec ファイルを確認する
2. 既存の設計方針と矛盾しないか確認する
3. 不明点があれば質問する

### 実装中

1. Spec ファイルの tasks.md に沿って実装する
2. 型ヒントを必ず付与する
3. 既存コードのスタイルに合わせる

### 実装後

1. 関連する Spec ファイルの更新が必要か確認し、必要なら提案する
2. `ruff` でフォーマット・リントを確認する
3. 適切なコミットメッセージを提案する
4. 必要に応じて `docs/wiki/` 内のドキュメントを作成・更新する

## ディレクトリ構成

```
manganize/                      # Workspace ルート
├── AGENTS.md                   # このファイル
├── pyproject.toml              # Workspace 設定
├── uv.lock                     # 統合ロックファイル
├── main.py                     # CLI エントリーポイント
├── Taskfile.yml                # タスクランナー定義
├── alembic/                    # DBマイグレーション
│   ├── env.py
│   └── versions/
├── alembic.ini
├── characters/                 # キャラクター設定ファイル
├── docs/
│   ├── specs/                  # Spec ファイル（機能ごと）
│   └── wiki/                   # 開発者向け技術ドキュメント（Divio システム）
│       ├── tutorials/              # チュートリアル（学習指向）
│       ├── how-to/                 # ハウツーガイド（問題解決指向）
│       ├── reference/              # リファレンス（情報指向）
│       └── explanation/            # 解説（理解指向）
├── packages/
│   └── core/                   # コアエージェントパッケージ
│       ├── pyproject.toml      # manganize-core
│       ├── README.md
│       └── manganize_core/
│           ├── agents.py       # LangGraph エージェント定義
│           ├── prompts.py      # プロンプトテンプレート
│           ├── tools.py        # エージェントが使用するツール
│           ├── character.py    # キャラクター基底クラス
│           └── app.py          # アプリケーション主体
└── apps/
    └── web/                    # Web アプリケーションパッケージ
        ├── pyproject.toml      # manganize-web
        ├── README.md
        └── manganize_web/
            ├── main.py         # FastAPI エントリーポイント
            ├── config.py       # 設定管理
            ├── templates.py    # Jinja2 テンプレート設定
            ├── api/            # API エンドポイント
            ├── models/         # SQLAlchemy モデル
            ├── repositories/   # データアクセス層
            ├── schemas/        # Pydantic スキーマ
            ├── services/       # ビジネスロジック
            ├── utils/          # ユーティリティ
            ├── templates/      # Jinja2 テンプレート
            └── static/         # CSS/JS
```

## 注意事項

- **仕様と実装の同期を最優先**: コードを変更したら、対応する Spec ファイルの更新も検討する
- **機能ごとに Spec を分離**: 1 つの巨大な Spec ファイルを作らない
- **EARS 記法を守る**: requirements.md では曖昧な表現を避け、EARS パターンに従う
- **ドキュメントの更新**: 開発によってドキュメントの作成や更新が必要な場合は、`docs/wiki/` 内のコンテンツを適宜更新する。Divio システムの4象限（Tutorials / How-to / Reference / Explanation）に沿って適切な場所に配置すること

