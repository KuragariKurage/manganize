# API Endpoints Reference

**対象**: Manganize Web App

このドキュメントは、Manganize Web アプリケーションで提供されるすべての API エンドポイントのリファレンスです。

## 目次

- [Generation API](#generation-api)
- [Character API](#character-api)
- [History API](#history-api)
- [Health Check](#health-check)

---

## Generation API

マンガ画像の生成に関連するエンドポイント。

### POST /api/generate

マンガ生成リクエストを作成します。

**Request Body (Form Data)**:
- `topic` (string, required): マンガにしたいトピック (1-50000文字)
- `character` (string, required): 使用するキャラクター名

**Response**: HTML partial (`partials/progress.html`)

**Example**:
```bash
curl -X POST http://localhost:8000/api/generate \
  -F "topic=Transformerアーキテクチャについて" \
  -F "character=kurage"
```

---

### GET /api/generate/{generation_id}/stream

生成進捗をSSE（Server-Sent Events）でストリーミングします。

**Path Parameters**:
- `generation_id` (string, required): 生成リクエストのUUID

**Response**: Server-Sent Events (SSE)

**Event Format**:
```json
{
  "event": "progress",
  "data": {
    "id": "uuid",
    "status": "researching|writing|generating|completed|error",
    "message": "進捗メッセージ",
    "progress": 0-100
  }
}
```

**Example**:
```javascript
const eventSource = new EventSource('/api/generate/{generation_id}/stream');
eventSource.addEventListener('progress', (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
});
```

---

### GET /api/generate/{generation_id}/result

生成結果をHTML partialとして取得します。

**Path Parameters**:
- `generation_id` (string, required): 生成リクエストのUUID

**Response**: HTML partial (`partials/result.html`)

---

### POST /api/upload

ファイルをアップロードしてテキストを抽出します。

**Request Body (Form Data)**:
- `file` (file, required): アップロードするファイル (.txt, .pdf, .md, .markdown)
  - 最大サイズ: 10MB

**Response**:
```json
{
  "text": "抽出されたテキスト",
  "filename": "ファイル名"
}
```

**Errors**:
- `400 Bad Request`: ファイルサイズ超過、サポートされていない形式、テキスト抽出失敗
- `500 Internal Server Error`: その他の処理エラー

**Example**:
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf"
```

---

### GET /api/images/{generation_id}

生成されたマンガ画像を取得します。

**Path Parameters**:
- `generation_id` (string, required): 生成リクエストのUUID

**Response**: PNG image (Content-Type: image/png)

**Cache**: `Cache-Control: public, max-age=31536000`

---

### GET /api/images/{generation_id}/download

生成されたマンガ画像をダウンロード用のファイル名でダウンロードします。

**Path Parameters**:
- `generation_id` (string, required): 生成リクエストのUUID

**Response**: PNG image with `Content-Disposition: attachment`

**Filename Format**: `manganize_{datetime}_{title}.png`

---

### GET /api/images/{generation_id}/thumbnail

生成されたマンガ画像のサムネイル（200x200）を取得します。

**Path Parameters**:
- `generation_id` (string, required): 生成リクエストのUUID

**Response**: PNG image (200x200, アスペクト比維持)

**Cache**: `Cache-Control: public, max-age=31536000`

---

## Character API

キャラクター管理に関連するエンドポイント。

### GET /api/characters

すべてのキャラクターのリストを取得します。

**Response**:
```json
[
  {
    "name": "kurage",
    "display_name": "くらげちゃん",
    "nickname": "くらげ",
    "attributes": ["可愛い", "天然"],
    "personality": "明るくて前向き",
    "speech_style": {
      "tone": "カジュアル",
      "patterns": ["〜だよ", "〜ね"],
      "examples": ["こんにちは！"],
      "forbidden": ["です", "ます"]
    },
    "is_default": true
  }
]
```

---

### GET /api/characters/{name}

特定のキャラクターの詳細を取得します。

**Path Parameters**:
- `name` (string, required): キャラクター名

**Response**: Character object (JSON)

**Errors**:
- `404 Not Found`: キャラクターが存在しない

---

### POST /api/characters

新しいキャラクターを作成します。

**Request Body (JSON)**:
```json
{
  "name": "new_character",
  "display_name": "新キャラ",
  "nickname": "キャラ",
  "attributes": ["属性1", "属性2"],
  "personality": "性格説明",
  "speech_style": {
    "tone": "口調",
    "patterns": ["パターン1"],
    "examples": ["例文"],
    "forbidden": ["禁止語"]
  }
}
```

**Response**: Created character (JSON)

**Errors**:
- `400 Bad Request`: バリデーションエラー
- `409 Conflict`: 同名のキャラクターが既に存在

---

### PUT /api/characters/{name}

既存のキャラクターを更新します。

**Path Parameters**:
- `name` (string, required): キャラクター名

**Request Body (JSON)**: POST と同じ形式

**Response**: Updated character (JSON)

**Errors**:
- `400 Bad Request`: デフォルトキャラクターは更新不可
- `404 Not Found`: キャラクターが存在しない

---

### DELETE /api/characters/{name}

キャラクターを削除します。

**Path Parameters**:
- `name` (string, required): キャラクター名

**Response**: `204 No Content`

**Errors**:
- `400 Bad Request`: デフォルトキャラクターは削除不可
- `404 Not Found`: キャラクターが存在しない

---

## History API

生成履歴の管理に関連するエンドポイント。

### GET /api/history

生成履歴のリストをページネーション付きで取得します。

**Query Parameters**:
- `page` (integer, default: 1): ページ番号
- `limit` (integer, default: 10): 1ページあたりの件数

**Response**: HTML partial (`partials/history_list.html`)

**Features**:
- 無限スクロール対応 (HTMX `hx-trigger="revealed"`)
- サムネイル表示
- 作成日時の降順でソート

---

### GET /api/history/{generation_id}

特定の生成履歴の詳細を取得します。

**Path Parameters**:
- `generation_id` (string, required): 生成リクエストのUUID

**Response**:
```json
{
  "id": "uuid",
  "character_name": "kurage",
  "input_topic": "トピック",
  "generated_title": "生成されたタイトル",
  "status": "completed",
  "error_message": null,
  "created_at": "2025-12-28T12:00:00Z",
  "completed_at": "2025-12-28T12:05:00Z"
}
```

**Errors**:
- `404 Not Found`: 履歴が存在しない

---

### DELETE /api/history/{generation_id}

生成履歴を削除します。

**Path Parameters**:
- `generation_id` (string, required): 生成リクエストのUUID

**Response**: Empty HTML (for HTMX `hx-swap="outerHTML"`)

**Errors**:
- `404 Not Found`: 履歴が存在しない

---

## Health Check

### GET /health

アプリケーションの健全性を確認します。

**Response**:
```json
{
  "status": "ok"
}
```

---

## Error Responses

すべてのエラーレスポンスは以下の形式で返されます：

```json
{
  "detail": "エラーメッセージ"
}
```

### HTTP Status Codes

- `200 OK`: 成功
- `201 Created`: リソース作成成功
- `204 No Content`: 削除成功
- `400 Bad Request`: リクエストが不正
- `404 Not Found`: リソースが見つからない
- `409 Conflict`: リソースが既に存在
- `500 Internal Server Error`: サーバーエラー

---

## Rate Limiting

すべてのエンドポイントには、IPアドレスごとにレート制限が適用されます。

- **制限**: 10リクエスト/分/IP
- **実装**: slowapi

レート制限を超えた場合、`429 Too Many Requests` が返されます。

---

## CORS

デフォルトでは `http://localhost:3000` からのCORSリクエストが許可されています。

設定は `web/config.py` の `cors_origins` で変更可能です。

---

## Authentication

現在、認証は実装されていません。将来的にはAPIキー認証やOAuth2の追加を検討しています。

---

## WebSocket Support

現在、WebSocketは使用していません。リアルタイム通信にはSSE（Server-Sent Events）を使用しています。

---

## Versioning

APIバージョニングは現在未実装です。破壊的変更が必要な場合は、`/api/v2/` などのプレフィックスを追加します。

---

## 関連ドキュメント

- [How-to: 本番環境へのデプロイ](../how-to/deploy-production.md)
- [Tutorial: 最初のマンガを生成する](../tutorials/first-manga.md)
- [Specification: Web App Requirements](../../specs/001-web-app/requirements.md)
