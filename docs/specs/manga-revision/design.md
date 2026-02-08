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

対象: `templates/partials/result.html` を拡張。

### UI 挙動

- `修正する` ボタンで修正モード開始。
- クリックで `point` 追加、ドラッグで `box` 追加。
- 各ターゲットに対し指示入力フォームを表示。
- `修正を実行` で JSON を API に送信。

### イベントモデル

- 画像上のオーバーレイは Canvas で管理。
- ターゲットはクライアント状態として保持し、送信時に正規化座標へ変換。

### UX 制約

- ターゲット数が 5 を超える場合は追加不可。
- 指示未入力のターゲットがある場合は送信不可。

---

## 進捗・履歴表示

- 既存 progress partial と result partial を流用。
- result には「この画像はリビジョン」「親画像へ移動」リンクを追加。
- history list には `v1 / v2 / v3` 相当の表示を将来的に追加可能な構造にする。

---

## 移行計画

1. Alembic で `generation_history` 拡張。
2. Pydantic schema 追加（Revision 系）。
3. API / Service / Repository 実装。
4. Core 編集関数の実装。
5. result UI に修正モード追加。
6. 最低限の統合テスト追加。

---

## テスト戦略

- API バリデーションテスト（point / box / 上限 / 範囲外）
- リビジョン作成から SSE 完了までの統合テスト
- 親子関係保存テスト
- 既存初回生成フローの回帰テスト

---

## Non-Goals（MVP）

- 画像生成モデル切替 UI / 設定管理
- 履歴ページでの世代ツリー可視化（v1/v2/v3 表示）
- `expected_text` に対する自動 OCR 照合
