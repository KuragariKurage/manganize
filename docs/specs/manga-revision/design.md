# マンガ修正機能 アーキテクチャ設計

## 概要

本機能は、生成済み画像に対してユーザーが位置指定 (`point` / `box`) と自由指示を与え、
新しいリビジョン画像を生成する仕組みを追加する。

既存の「初回生成」フローは維持し、リビジョン生成は別ユースケースとして追加する。

---

## 設計方針

1. **自由修正を最優先**: 文字修正専用 API にしない。
2. **位置指定は2種類**: `point` と `box` を同一 API で受ける。
3. **正規化座標**: 画面サイズ差異に影響されないよう 0-1 座標を保存。
4. **履歴系譜を保持**: 親画像 ID を持つリビジョンとして保存。
5. **既存互換性**: 初回生成 API / SSE を壊さず機能追加。

## MVP 決定事項（2026-02-08）

1. **モデル方針**: 現行の画像生成モデルをそのまま利用する（モデル切替機構は今回のスコープ外）。
2. **履歴 UI**: 初期リリースは「親画像リンク表示」のみ実装し、世代ラベル（v1/v2 など）は将来対応とする。
3. **OCR 検証**: `expected_text` の自動 OCR 検証は MVP に含めない。
4. **マーカー色**: `point` / `box` / 番号バッジはオレンジ基調で統一する。
5. **入力導線**: ターゲット追加直後にインラインツールチップを表示し、その場で指示入力する。
6. **画面構成**: 修正 UI は結果 partial 内ではなく、専用ワークスペース画面として提供する。
7. **ツールチップ制御**: 同時表示は 1 つのみとし、ターゲット切替時は既存ツールチップを閉じる。
8. **再確認導線**: 追加済み修正は常時表示の「修正一覧」から再確認・再編集できるようにする。

---

## データモデル設計

`generation_history` テーブルを拡張する。

### 追加カラム

- `generation_type: str` (`initial` / `revision`)
- `parent_generation_id: str | None`（自己参照 FK）
- `revision_payload: JSON | None`（修正指示のスナップショット）

### revision_payload 例

```json
{
  "global_instruction": "全体の色味を少し明るく",
  "edits": [
    {
      "target": {"kind": "point", "x": 0.62, "y": 0.31, "radius": 0.04},
      "instruction": "このキャラの口を閉じて笑顔に",
      "edit_type": "illustration"
    },
    {
      "target": {"kind": "box", "x": 0.12, "y": 0.55, "w": 0.28, "h": 0.18},
      "instruction": "この吹き出しを『こんにちは』に",
      "edit_type": "text",
      "expected_text": "こんにちは"
    }
  ]
}
```

### 採用理由

- 既存履歴 API / UI を流用しやすい。
- リビジョン生成も 1 つの generation として扱える。
- JSON 保存で仕様変更に追従しやすい。

---

## API 設計

### 1) リビジョン作成

`POST /api/generations/{generation_id}/revisions`

Request (JSON):

```json
{
  "global_instruction": "任意",
  "edits": [
    {
      "target": {"kind": "point", "x": 0.5, "y": 0.5, "radius": 0.04},
      "instruction": "任意の自由修正指示",
      "edit_type": "auto",
      "expected_text": null
    }
  ]
}
```

Response:

```json
{
  "generation_id": "new_revision_id"
}
```

### 2) 進捗 / 結果取得

既存の以下を流用:
- `GET /api/generate/{generation_id}/stream`
- `GET /api/generate/{generation_id}/result`

`generation_type=revision` のときは、内部でリビジョン生成分岐を実行する。

### 3) バリデーション制約

- `edits` は 1-5 件
- `instruction` は 1-300 文字
- `target.kind in {point, box}`
- `point`: `x,y in [0,1]`, `radius in (0,0.2]`（未指定時デフォルト 0.04）
- `box`: `x,y,w,h in [0,1]`, `w>0`, `h>0`, `x+w<=1`, `y+h<=1`
- `expected_text` は任意（`edit_type=text` 以外でも許容）

### 4) 修正ワークスペース画面

`GET /generations/{generation_id}/revision-workspace`

- 目的: 修正専用 UI（領域選択・インライン入力・比較表示）を別画面で提供する。
- 画面内で使うデータ:
  - 親 generation 情報（タイトル、画像 URL）
  - 既存 revision（任意）

既存 API との関係:
- 修正送信は引き続き `POST /api/generations/{generation_id}/revisions` を使用。
- 進捗監視は既存 SSE (`/api/generate/{generation_id}/stream`) を使用。

---

## バックエンド実装設計

## Service Layer

`GeneratorService` に以下を追加:

- `create_revision_request(parent_generation_id, payload, db_session) -> revision_id`
- `generate_revision(generation_id, db_session) -> AsyncGenerator[GenerationStatus, None]`

`stream_generation_progress` で generation を参照し、
`generation_type` によって `generate_manga` / `generate_revision` を切り替える。

## Repository Layer

`GenerationRepository` に以下を追加:

- `create_revision(...)`
- `get_parent(generation_id)`
- `list_revisions(parent_generation_id)`（将来 UI 用）

---

## Core (manganize_core) 実装設計

`tools.py` に編集専用関数を追加:

- `edit_manga_image(base_image: bytes, scenario: str, revision_payload: dict, character: BaseCharacter) -> bytes | None`

### 編集入力の渡し方

- `contents` に以下を含める:
  - 親画像 (`base_image`)
  - キャラクター参照画像（既存どおり）
  - 構造化指示テキスト（global + edits）

### point の扱い

- `point` は内部で疑似領域 (`radius`) として文章化。
- 必要に応じてガイド画像（マーカー付き）を生成して入力に添付。

### プロンプトの要点

- 指定領域を最優先で修正。
- 非指定領域は可能な限り維持。
- `expected_text` がある場合は文字列一致を優先。

---

## フロントエンド設計

### テンプレート構成

- `templates/revision_workspace.html`（新規）
  - 修正前後比較レイアウト（2 カラム）
  - 左: 修正前画像 + 編集キャンバス
  - 右: 修正後プレビュー（未生成時はプレースホルダ）
- `templates/partials/result.html`
  - `修正する` ボタンの遷移先を修正ワークスペースへ変更

### オーバーレイ描画仕様

Canvas レイヤーでターゲットを描画し、以下のスタイルトークンを採用:

- `markerStroke = #f97316`（orange-500 相当）
- `markerFill = #f97316`
- `markerText = #ffffff`
- `badgeRadius = 12px`（既存より拡大）
- `badgeFont = 12px-13px semibold`

描画ルール:

- `point`: 円 + 中心ドット + 番号バッジ
- `box`: オレンジ矩形 + 左上付近に番号バッジ
- ドラッグ中の下書き矩形もオレンジ破線で表示

### インラインツールチップ入力仕様

ターゲット作成時に編集ポップアップを即時表示する。

- 表示契機:
  - 新規ターゲット作成直後
  - 既存バッジクリック時
- 表示位置:
  - `point`: クリック位置の右上
  - `box`: ボックス右上（画面外にはみ出す場合は反転）
- 入力項目:
  - `instruction`（必須）
  - `edit_type`（任意）
  - `expected_text`（任意）
- 操作:
  - `保存` でツールチップを閉じる
  - `削除` で対象ターゲットを削除
  - `Esc` でキャンセル（未保存変更は確認ダイアログ）
  - 同時に開けるツールチップは 1 つのみ
  - 別ターゲット選択時は、現在の編集中ツールチップを閉じて対象ターゲットへ切替
  - 未保存で切替える場合は `保存して移動 / 破棄して移動` を確認ダイアログで選択

### 修正一覧パネル仕様

- 位置:
  - Desktop: 右カラム（比較 UI と同居）
  - Mobile: 下部固定パネル
- 表示項目:
  - `#番号`
  - ターゲット種別（点/矩形）
  - 指示文の要約（20-30文字）
  - ステータス（`未完了` / `完了`）
- 操作:
  - 一覧行クリックで対応ターゲットのツールチップを開く
  - 現在編集中のターゲットはハイライト表示
  - 未完了項目がある場合は実行ボタンを無効化

### 比較 UI 仕様（修正前後）

- 同一画面で before / after を横並び表示。
- after 側は状態を持つ:
  - `idle`: まだ修正実行していない
  - `processing`: 進捗表示
  - `completed`: 修正後画像表示
  - `error`: エラー表示 + 再実行導線
- 比較時の誤認防止:
  - 両画像にラベル（修正前 / 修正後）を固定表示
  - 同一アスペクト比ボックスに収める

### イベントモデル

- 編集状態:
  - `edits: RevisionEdit[]`
  - `activeEditId: string | null`（ツールチップ編集中ターゲット）
  - `revisionResultId: string | null`（直近修正結果）
  - `dirtyEditId: string | null`（未保存状態のターゲット）
- 画像上のオーバーレイは Canvas で管理。
- ターゲットはクライアント状態として保持し、送信時に正規化座標へ変換。
- 指示未入力ターゲットがある場合は `修正を実行` を無効化。

---

## 進捗・履歴表示

- 修正ワークスペース内で既存 SSE ストリームを購読し進捗を更新。
- result には従来どおり「この画像はリビジョン」「親画像へ移動」リンクを表示。
- history list には `v1 / v2 / v3` 相当の表示を将来的に追加可能な構造にする。

---

## 移行計画

1. Alembic で `generation_history` 拡張。
2. Pydantic schema 追加（Revision 系）。
3. API / Service / Repository 実装。
4. Core 編集関数の実装。
5. result UI に修正モード追加。
6. 最低限の統合テスト追加。
7. 修正ワークスペース画面を追加し、result から遷移可能にする。
8. インラインツールチップ入力に置き換え、スクロール依存入力を廃止する。
9. 比較表示（before / after）を修正ワークスペースに追加する。

---

## テスト戦略

- API バリデーションテスト（point / box / 上限 / 範囲外）
- リビジョン作成から SSE 完了までの統合テスト
- 親子関係保存テスト
- 既存初回生成フローの回帰テスト
- フロントエンド E2E:
  - ターゲット作成時にツールチップが開くこと
  - ツールチップが同時に 1 つのみ表示されること
  - 未保存切替時に確認ダイアログが出ること
  - 修正一覧から再編集導線に遷移できること
  - オレンジマーカーと白字番号バッジが描画されること
  - 修正前後比較領域が状態遷移すること

---

## Non-Goals（MVP）

- 画像生成モデル切替 UI / 設定管理
- 履歴ページでの世代ツリー可視化（v1/v2/v3 表示）
- `expected_text` に対する自動 OCR 照合
