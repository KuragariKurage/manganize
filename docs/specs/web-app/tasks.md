# Web アプリ 実装タスク一覧

## 概要

このドキュメントは、manganize Web アプリの実装タスクを管理する。
タスクは優先度順に並べられ、依存関係を考慮した順序で実装する。

## タスク運用ルール（リアルタイム更新）

- タスク着手時に、対象タスク行へ `（進行中）` を追記して即時反映する
- タスク完了時に `（進行中）` を削除し、チェックボックスを `[x]` に更新する
- ブロッカー発生時は、対象タスク直下に `BLOCKED:` で理由と対応方針を追記する
- 進捗サマリー表（完了数・進捗率）は、タスク状態更新と同じタイミングで更新する

---

## Phase 0.5: S3互換アップロード移行（完了）

- [x] **T-UPL-001**: `StorageBackend` 抽象化と S3 互換実装を追加
  - AWS S3 / Cloudflare R2 / MinIO を環境変数で切替可能にする

- [x] **T-UPL-002**: `upload_sources` テーブルと `generation_history.source_upload_id` を追加
  - `upload_id -> object_key` メタデータ管理を導入

- [x] **T-UPL-003**: `POST /api/upload` を object storage 保存 + `upload_id` 返却に変更
  - ローカル永続ディスクを使わないアップロード処理へ変更

- [x] **T-UPL-004**: `POST /api/generate` を `upload_id` 対応に変更
  - 生成時に署名付き URL を解決し、Agent 入力へ組み込む

- [x] **T-UPL-005**: フロントフォームを `upload_id` 送信方式へ更新
  - `topic` または `upload_id` があれば生成可能に変更

---

## Phase 1: プロジェクトセットアップ

### Backend

- [ ] **T-BE-001**: `backend/` ディレクトリ構造の作成
  - `app/`, `app/api/`, `app/models/`, `app/schemas/`, `app/services/` を作成
  - `__init__.py` ファイルを配置

- [ ] **T-BE-002**: `backend/requirements.txt` の作成
  - FastAPI, SQLAlchemy, Pydantic, sse-starlette, aiosqlite を追加
  - manganize パッケージへの参照を設定

- [ ] **T-BE-003**: FastAPI アプリケーションの基本設定
  - `app/main.py` に FastAPI インスタンスを作成
  - CORS 設定を追加
  - ヘルスチェックエンドポイントを追加

### Frontend

- [ ] **T-FE-001**: Next.js プロジェクトの初期化
  - `npx create-next-app@latest frontend` で作成
  - App Router, TypeScript, Tailwind CSS を選択

- [ ] **T-FE-002**: 基本レイアウトの作成
  - `app/layout.tsx` にヘッダー、ナビゲーションを追加
  - グローバルスタイルの設定

---

## Phase 2: バックエンド実装

### データベース

- [ ] **T-BE-004**: SQLAlchemy セットアップ
  - `app/models/database.py` に DB 接続設定を作成
  - async session factory の設定

- [ ] **T-BE-005**: GenerationHistory モデルの作成
  - `app/models/history.py` にモデル定義
  - マイグレーションスクリプトの作成（オプション）

### スキーマ

- [ ] **T-BE-006**: Pydantic スキーマの作成
  - `app/schemas/generation.py` に以下を定義:
    - `GenerationRequest`
    - `GenerationResponse`
    - `ProgressEvent`
    - `HistoryItem`
    - `HistoryDetail`

### サービス層

- [ ] **T-BE-007**: GeneratorService の実装
  - `app/services/generator.py` に ManganizeAgent のラッパーを作成
  - 進捗状態の管理機能を追加
  - 非同期生成メソッドの実装

- [ ] **T-BE-008**: 進捗通知機能の実装
  - asyncio.Queue を使用した進捗イベントの配信
  - SSE イベント生成ロジック

### API エンドポイント

- [ ] **T-BE-009**: 生成 API の実装
  - `POST /api/generate` - 生成リクエスト受付
  - `GET /api/generate/{id}/stream` - SSE ストリーム

- [ ] **T-BE-010**: 画像 API の実装
  - `GET /api/images/{id}` - 画像取得
  - `GET /api/images/{id}/thumbnail` - サムネイル取得（オプション）

- [ ] **T-BE-011**: 履歴 API の実装
  - `GET /api/history` - 履歴一覧
  - `GET /api/history/{id}` - 履歴詳細
  - `DELETE /api/history/{id}` - 履歴削除

### テスト

- [ ] **T-BE-012**: API テストの作成
  - pytest + httpx を使用
  - 各エンドポイントの基本テスト

---

## Phase 3: フロントエンド実装

### コンポーネント

- [ ] **T-FE-003**: TextInput コンポーネントの作成
  - テキストエリア
  - 文字数カウント表示
  - 入力状態の管理

- [ ] **T-FE-004**: FileUpload コンポーネントの作成
  - ドラッグ＆ドロップゾーン
  - ファイル形式検証（.txt, .md）
  - ファイル内容の読み込み

- [ ] **T-FE-005**: ProgressIndicator コンポーネントの作成
  - 進捗段階の表示
  - アニメーション
  - エラー表示

- [ ] **T-FE-006**: ImageViewer コンポーネントの作成
  - 画像表示
  - ダウンロードボタン
  - ローディング状態

- [ ] **T-FE-007**: HistoryList コンポーネントの作成
  - グリッドレイアウト
  - サムネイル表示
  - 削除ボタン

### ページ

- [ ] **T-FE-008**: メインページの実装
  - TextInput + FileUpload の統合
  - 生成ボタンのロジック
  - ProgressIndicator + ImageViewer の表示切り替え

- [ ] **T-FE-009**: 履歴ページの実装
  - HistoryList の表示
  - ページネーション or 無限スクロール
  - 詳細モーダル

### API クライアント

- [ ] **T-FE-010**: API クライアントの実装
  - `lib/api.ts` に fetch ラッパーを作成
  - SSE クライアントの実装
  - エラーハンドリング

### スタイリング

- [ ] **T-FE-011**: レスポンシブデザインの適用
  - モバイル対応
  - ダークモード対応（オプション）

---

## Phase 4: 統合・テスト

- [ ] **T-INT-001**: バックエンド・フロントエンド統合テスト
  - 生成フローの E2E テスト
  - エラーケースのテスト

- [ ] **T-INT-002**: パフォーマンス検証
  - SSE 遅延の測定
  - 大きなテキスト入力のテスト

---

## Phase 5: ドキュメント・仕上げ

- [ ] **T-DOC-001**: README の更新
  - 起動方法の記載
  - 環境変数の説明

- [ ] **T-DOC-002**: 開発者向けドキュメント
  - `docs/wiki/` に How-to ガイドを追加

---

## 進捗サマリー

| Phase | 完了 | 合計 | 進捗率 |
|-------|------|------|--------|
| Phase 1 | 0 | 5 | 0% |
| Phase 2 | 0 | 9 | 0% |
| Phase 3 | 0 | 9 | 0% |
| Phase 4 | 0 | 2 | 0% |
| Phase 5 | 0 | 2 | 0% |
| **合計** | **0** | **27** | **0%** |

### S3互換アップロード移行 進捗

| Phase | 完了 | 合計 | 進捗率 |
|-------|------|------|--------|
| Phase 0.5 | 5 | 5 | 100% |
