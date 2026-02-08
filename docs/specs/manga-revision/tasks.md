# マンガ修正機能 実装タスク一覧

## タスク運用ルール（リアルタイム更新）

- タスク着手時に、対象タスク行へ `（進行中）` を追記して即時反映する
- タスク完了時に `（進行中）` を削除し、チェックボックスを `[x]` に更新する
- ブロッカー発生時は、対象タスク直下に `BLOCKED:` で理由と対応方針を追記する
- 実装中にスコープ変更が起きた場合は、その場でタスク分解・追加・削除を行い、`tasks.md` を最新化する

## Phase 1: スキーマ・モデル

- [x] **T-REV-001**: Alembic マイグレーション作成
  - `generation_history` に `generation_type`, `parent_generation_id`, `revision_payload` を追加
  - 既存データを `generation_type=initial` で埋める

- [x] **T-REV-002**: SQLAlchemy モデル更新
  - `apps/web/manganize_web/models/generation.py` を拡張
  - 自己参照 FK を定義

- [x] **T-REV-003**: Pydantic スキーマ追加
  - `RevisionTargetPoint`, `RevisionTargetBox`, `RevisionEdit`, `CreateRevisionRequest`
  - 入力バリデーション（件数・座標範囲・文字数）

## Phase 2: バックエンド API / サービス

- [x] **T-REV-004**: Repository 拡張
  - `create_revision`, `get_parent`, `list_revisions` を追加

- [x] **T-REV-005**: GeneratorService 拡張
  - `create_revision_request` 実装
  - `generate_revision` 実装
  - 既存 `generate_manga` との分岐導入

- [x] **T-REV-006**: リビジョン API 実装
  - `POST /api/generations/{generation_id}/revisions`
  - 既存 SSE / result エンドポイントで revision を処理可能にする

## Phase 3: core 画像編集

- [x] **T-REV-007**: `edit_manga_image` 追加
  - `packages/core/manganize_core/tools.py` に編集専用関数を実装
  - 親画像 + 修正指示を用いた再生成処理
  - MVP は現行画像生成モデルを利用（モデル切替実装は行わない）

- [x] **T-REV-008**: 編集プロンプト整備
  - `packages/core/manganize_core/prompts.py` に編集用 system prompt を追加
  - 「指定領域優先」「非指定領域維持」を明示

## Phase 4: フロントエンド

- [x] **T-REV-009**: 結果画面に修正モード追加
  - クリックで `point`、ドラッグで `box`
  - オーバーレイ描画

- [x] **T-REV-010**: 修正指示フォーム実装
  - `instruction` 必須
  - `edit_type` / `expected_text` 任意
  - ターゲット削除・件数上限 UI

- [x] **T-REV-011**: リビジョン送信フロー実装
  - JSON API 呼び出し
  - 生成中 UI と結果表示を既存フローに接続
  - 結果画面に親画像リンクを表示（世代ラベル表示は対象外）

## Phase 5: テスト・仕上げ

- [ ] **T-REV-012**: API バリデーションテスト
  - point/box 正常系
  - 範囲外・件数超過・空指示 異常系

- [ ] **T-REV-013**: 統合テスト
  - リビジョン作成→SSE完了→結果取得
  - 親子関係保存確認

- [ ] **T-REV-014**: 回帰確認
  - 既存通常生成フローの非破壊確認

- [ ] **T-REV-015**: ドキュメント更新
  - `apps/web/README.md` に修正機能の利用方法を追記
  - 必要に応じて `docs/wiki/` に How-to を追加
  - OCR 自動検証は未実装（MVP 範囲外）であることを明記

## Phase 6: UX 改善（2026-02-08 要望対応）

- [ ] **T-REV-016**: 修正ワークスペース画面の追加
  - `GET /generations/{generation_id}/revision-workspace` を追加
  - `result` 画面の「修正する」から専用画面へ遷移
  - 既存 result partial 内の編集 UI は簡素化または撤去

- [ ] **T-REV-017**: オーバーレイ色・番号バッジ改善
  - `point` / `box` / 補助表示をオレンジ配色へ統一
  - 番号を「オレンジの円 + 白文字」で描画
  - バッジサイズとフォントサイズを視認性重視で調整

- [ ] **T-REV-018**: インラインツールチップ入力実装
  - ターゲット追加直後にポップアップを表示
  - `instruction` / `edit_type` / `expected_text` をその場入力
  - バッジクリックで再編集、Esc キャンセル、削除導線を実装
  - 同時表示 1 件制御、および未保存切替時の確認ダイアログを実装

- [ ] **T-REV-021**: 修正一覧パネル実装
  - `#番号 / 種別 / 指示要約 / 完了状態` を常時表示
  - 一覧クリックで該当ターゲットのツールチップを開く
  - Desktop 右カラム / Mobile 下部パネルに対応

- [ ] **T-REV-019**: 修正前後比較 UI 実装
  - before / after の2カラム比較表示
  - 未生成 / 生成中 / 完了 / エラー状態を表現
  - 修正実行後に after 側を自動更新

- [ ] **T-REV-020**: UX 回帰テスト追加
  - インライン入力導線でスクロール不要であることを確認
  - マーカー色と番号バッジ描画の回帰確認
  - 同時ツールチップ 1 件制御と未保存切替ダイアログの確認
  - 修正一覧から再編集できることを確認
  - 比較 UI の状態遷移確認
