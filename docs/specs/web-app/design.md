# Web アプリ アーキテクチャ設計

## 概要

manganize Web アプリは、FastAPI バックエンドと Next.js フロントエンドで構成される。
バックエンドは既存の `ManganizeAgent` をラップし、REST API と SSE（Server-Sent Events）で
フロントエンドと通信する。

---

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                         │
├─────────────────────────────────────────────────────────────────┤
│  Next.js (App Router)                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Main Page   │  │ History Page │  │  Components  │          │
│  │  (page.tsx)  │  │  (page.tsx)  │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP / SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  API Routes  │  │   Services   │  │    Models    │          │
│  │  (routes.py) │  │(generator.py)│  │ (history.py) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│           │                │                  │                  │
│           └────────────────┼──────────────────┘                  │
│                            ▼                                     │
│                   ┌──────────────┐                               │
│                   │ManganizeAgent│                               │
│                   │(manganize/)  │                               │
│                   └──────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │    SQLite    │
                     │  (data.db)   │
                     └──────────────┘
```

---

## ディレクトリ構成

```
manganize/
├── manganize/                  # 既存のコアエージェント
│   ├── agents.py
│   ├── prompts.py
│   └── tools.py
├── backend/                    # FastAPI アプリケーション
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI エントリーポイント
│   │   ├── config.py           # 設定管理
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py       # API ルート定義
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── database.py     # DB 接続設定
│   │   │   └── history.py      # 履歴モデル
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── generation.py   # Pydantic スキーマ
│   │   └── services/
│   │       ├── __init__.py
│   │       └── generator.py    # ManganizeAgent ラッパー
│   └── requirements.txt
├── frontend/                   # Next.js アプリケーション
│   ├── app/
│   │   ├── layout.tsx          # 共通レイアウト
│   │   ├── page.tsx            # メインページ
│   │   ├── history/
│   │   │   └── page.tsx        # 履歴ページ
│   │   └── globals.css         # グローバルスタイル
│   ├── components/
│   │   ├── TextInput.tsx       # テキスト入力コンポーネント
│   │   ├── FileUpload.tsx      # ファイルアップロード
│   │   ├── ProgressIndicator.tsx # 進捗表示
│   │   ├── ImageViewer.tsx     # 画像表示
│   │   └── HistoryList.tsx     # 履歴一覧
│   ├── lib/
│   │   └── api.ts              # API クライアント
│   ├── package.json
│   └── tsconfig.json
└── docs/specs/web-app/         # 仕様書
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

---

## バックエンド設計

### 技術スタック

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| FastAPI | ^0.115 | Web フレームワーク |
| SQLAlchemy | ^2.0 | ORM |
| Pydantic | ^2.0 | データバリデーション |
| sse-starlette | ^2.0 | Server-Sent Events |
| aiosqlite | ^0.20 | 非同期 SQLite ドライバ |

### API エンドポイント

#### POST /api/generate

マンガ画像の生成を開始する。

**リクエスト**
```json
{
  "text": "string (入力テキスト)"
}
```

**レスポンス**
```json
{
  "generation_id": "uuid (生成リクエストのID)"
}
```

#### GET /api/generate/{generation_id}/stream

生成処理の進捗を SSE でストリーミングする。

**イベント形式**
```
event: progress
data: {"status": "researching", "message": "リサーチ中..."}

event: progress
data: {"status": "writing_scenario", "message": "シナリオ作成中..."}

event: progress
data: {"status": "generating_image", "message": "画像生成中..."}

event: complete
data: {"status": "completed", "image_url": "/api/images/{generation_id}"}

event: error
data: {"status": "error", "message": "エラーメッセージ"}
```

#### GET /api/images/{generation_id}

生成された画像を取得する。

**レスポンス**
- Content-Type: image/png
- Body: 画像バイナリ

#### GET /api/history

生成履歴の一覧を取得する。

**クエリパラメータ**
- `limit`: 取得件数（デフォルト: 20）
- `offset`: オフセット（デフォルト: 0）

**レスポンス**
```json
{
  "items": [
    {
      "id": "uuid",
      "created_at": "ISO8601 datetime",
      "thumbnail_url": "/api/images/{id}/thumbnail",
      "text_preview": "入力テキストの先頭100文字..."
    }
  ],
  "total": 100
}
```

#### GET /api/history/{id}

履歴の詳細を取得する。

**レスポンス**
```json
{
  "id": "uuid",
  "created_at": "ISO8601 datetime",
  "input_text": "完全な入力テキスト",
  "image_url": "/api/images/{id}"
}
```

#### DELETE /api/history/{id}

履歴を削除する。

**レスポンス**
```json
{
  "success": true
}
```

### データベースモデル

```python
class GenerationHistory(Base):
    __tablename__ = "generation_history"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

### サービス層

`GeneratorService` クラスは `ManganizeAgent` をラップし、進捗状態を管理する。

```python
class GeneratorService:
    def __init__(self):
        self.agent = ManganizeAgent()
        self._progress_callbacks: dict[str, Queue] = {}

    async def generate(self, generation_id: str, text: str) -> None:
        """非同期で生成処理を実行し、進捗を通知する"""
        ...

    async def get_progress_stream(self, generation_id: str) -> AsyncIterator[dict]:
        """進捗状態をストリーミングする"""
        ...
```

---

## フロントエンド設計

### 技術スタック

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| Next.js | ^15 | React フレームワーク |
| React | ^19 | UI ライブラリ |
| TypeScript | ^5 | 型安全な開発 |
| Tailwind CSS | ^4 | スタイリング |

### ページ構成

#### メインページ (`/`)

```
┌─────────────────────────────────────┐
│           ヘッダー                   │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │     テキスト入力エリア        │   │
│  │                             │   │
│  │  [ファイルをドロップ]         │   │
│  └─────────────────────────────┘   │
│         [生成する] ボタン           │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │     進捗表示 / 結果表示       │   │
│  │                             │   │
│  │     [ダウンロード] ボタン     │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

#### 履歴ページ (`/history`)

```
┌─────────────────────────────────────┐
│           ヘッダー                   │
├─────────────────────────────────────┤
│  ┌───────┐ ┌───────┐ ┌───────┐     │
│  │ thumb │ │ thumb │ │ thumb │     │
│  │ 日時  │ │ 日時  │ │ 日時  │     │
│  └───────┘ └───────┘ └───────┘     │
│  ┌───────┐ ┌───────┐ ┌───────┐     │
│  │ thumb │ │ thumb │ │ thumb │     │
│  │ 日時  │ │ 日時  │ │ 日時  │     │
│  └───────┘ └───────┘ └───────┘     │
│                                     │
│        [もっと見る] ボタン           │
└─────────────────────────────────────┘
```

### コンポーネント設計

#### TextInput

- テキストエリアコンポーネント
- ファイルドロップゾーンを統合
- 入力状態を親コンポーネントに通知

#### FileUpload

- ドラッグ＆ドロップ対応
- `.txt`, `.md` ファイルのみ受け付け
- ファイル内容をテキストとして読み込み

#### ProgressIndicator

- SSE で進捗状態を購読
- 段階ごとにアニメーション表示
- エラー時はリトライボタンを表示

#### ImageViewer

- 生成された画像を表示
- ズーム機能（オプション）
- ダウンロードボタン

#### HistoryList

- 履歴をグリッド表示
- 無限スクロールまたはページネーション
- 削除確認ダイアログ

### 状態管理

React の `useState` / `useReducer` を使用。
複雑な状態管理ライブラリは不要（デモ用途のため）。

```typescript
interface GenerationState {
  status: 'idle' | 'generating' | 'completed' | 'error';
  progress: ProgressStatus | null;
  generatedImage: string | null;
  error: string | null;
}
```

---

## 通信設計

### SSE（Server-Sent Events）フロー

```
Client                                    Server
   │                                         │
   │  POST /api/generate                     │
   │  {"text": "..."}                        │
   │ ───────────────────────────────────────►│
   │                                         │
   │  {"generation_id": "xxx"}               │
   │ ◄───────────────────────────────────────│
   │                                         │
   │  GET /api/generate/xxx/stream           │
   │ ───────────────────────────────────────►│
   │                                         │
   │  event: progress                        │
   │  data: {"status": "researching"}        │
   │ ◄───────────────────────────────────────│
   │                                         │
   │  event: progress                        │
   │  data: {"status": "writing_scenario"}   │
   │ ◄───────────────────────────────────────│
   │                                         │
   │  event: progress                        │
   │  data: {"status": "generating_image"}   │
   │ ◄───────────────────────────────────────│
   │                                         │
   │  event: complete                        │
   │  data: {"status": "completed", ...}     │
   │ ◄───────────────────────────────────────│
   │                                         │
```

### エラーハンドリング

1. **接続エラー**: 自動リトライ（最大 3 回、指数バックオフ）
2. **生成エラー**: エラーメッセージを表示、手動リトライオプション
3. **タイムアウト**: 5 分でタイムアウト、ユーザーに通知

---

## セキュリティ考慮事項

### 入力検証

- テキスト長: 最大 100,000 文字
- ファイルサイズ: 最大 10MB
- ファイル形式: `.txt`, `.md` のみ

### CORS 設定

開発環境では `localhost:3000` からのアクセスを許可。
本番環境では適切なオリジンのみを許可。

### レート制限

デモ用途のため、簡易的なレート制限を実装:
- 1 IP あたり 10 リクエスト/分

---

## デプロイメント考慮事項

### 開発環境

```bash
# バックエンド
cd backend && uv run uvicorn app.main:app --reload

# フロントエンド
cd frontend && npm run dev
```

### 本番環境（将来）

- バックエンド: Docker コンテナ、Gunicorn + Uvicorn workers
- フロントエンド: Vercel または静的ホスティング
- データベース: PostgreSQL（SQLite から移行）

