# Web アプリ アーキテクチャ設計

## 概要

manganize Web アプリは、FastAPI バックエンドと HTMX + Jinja2 フロントエンドで構成される。
バックエンドは既存の `ManganizeAgent` をラップし、REST API と SSE（Server-Sent Events）で
フロントエンドと通信する。サーバーサイドレンダリングを基本とし、動的な UI 更新は HTMX で実現する。

---

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                         │
├─────────────────────────────────────────────────────────────────┤
│  HTMX + TailwindCSS                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Main Page   │  │ History Page │  │  Components  │          │
│  │  (index.html)│  │(history.html)│  │  (partials/) │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  hx-get, hx-post, hx-swap, hx-ext="sse"                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP / SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐                                               │
│  │  API Layer   │  - ルーティング、バリデーション                │
│  │  (api/)      │  - レスポンス生成                             │
│  └──────────────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │Service Layer │  - ビジネスロジック                           │
│  │(services/)   │  - ManganizeAgent 連携                        │
│  └──────────────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │DatabaseSession│ - トランザクション管理 (Unit of Work)          │
│  │ (uow.py)     │  - Repository 集約                            │
│  └──────────────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────┐                           │
│  │   Repository Layer               │                           │
│  │   - GenerationRepository         │                           │
│  │   - CharacterRepository          │                           │
│  └──────────────────────────────────┘                           │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │    Models    │  │ManganizeAgent│                            │
│  │ (models/)    │  │(manganize/)  │                            │
│  └──────────────┘  └──────────────┘                            │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  Templates   │  │   Static     │                            │
│  │  (Jinja2)    │  │ (TailwindCSS)│                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │    SQLite    │
                     │  (data.db)   │
                     └──────────────┘
```

### レイヤ構成と責務

| レイヤ | 責務 | 実装場所 |
|--------|------|---------|
| **API Layer** | HTTP リクエスト/レスポンス処理、バリデーション | `web/api/` |
| **Service Layer** | ビジネスロジック、外部サービス連携 | `web/services/` |
| **DatabaseSession** | トランザクション管理、Repository 集約 | `web/repositories/database_session.py` |
| **Repository Layer** | データアクセスの抽象化、CRUD 操作 | `web/repositories/` |
| **Model Layer** | データ構造の定義、SQLAlchemy モデル | `web/models/` |

**Repository パターンと Unit of Work パターンの採用**:

- **Repository**: データアクセスロジックをカプセル化し、ビジネスロジックからデータベース操作を分離
- **Unit of Work (DatabaseSession)**: 複数の Repository を管理し、トランザクション境界を明確化
- **利点**: テスタビリティ向上、責務の明確化、将来のデータストア変更に柔軟に対応

---

## ディレクトリ構成

```
manganize/
├── manganize/                  # 既存のコアエージェント
│   ├── agents.py
│   ├── prompts.py
│   └── tools.py
├── web/                        # Web アプリケーション
│   ├── __init__.py
│   ├── main.py                 # FastAPI エントリーポイント
│   ├── config.py               # 設定管理
│   ├── api/
│   │   ├── __init__.py
│   │   └── generation.py       # 生成 API ルート
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # DB 接続設定
│   │   ├── generation.py       # 生成履歴モデル
│   │   └── character.py        # キャラクターモデル
│   ├── repositories/           # Repository Layer (データアクセス)
│   │   ├── __init__.py
│   │   ├── base.py             # BaseRepository (Generic CRUD)
│   │   ├── generation.py       # GenerationRepository
│   │   ├── character.py        # CharacterRepository
│   │   └── database_session.py # DatabaseSession (Unit of Work)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── generation.py       # Pydantic スキーマ
│   ├── services/
│   │   ├── __init__.py
│   │   └── generator.py        # ManganizeAgent ラッパー
│   ├── templates/              # Jinja2 テンプレート
│   │   ├── base.html           # ベーステンプレート
│   │   ├── index.html          # メインページ
│   │   ├── history.html        # 履歴ページ
│   │   ├── character.html      # キャラクターカスタマイズページ
│   │   └── partials/           # HTMX パーシャル
│   │       ├── progress.html   # 進捗表示
│   │       ├── result.html     # 結果表示
│   │       ├── history_list.html  # 履歴一覧
│   │       └── character_form.html # キャラクター編集フォーム
│   └── static/
│       ├── css/
│       │   └── output.css      # TailwindCSS ビルド出力
│       ├── js/
│       │   └── htmx.min.js     # HTMX ライブラリ
│       └── images/
├── characters/                 # キャラクター定義
│   └── kurage/
│       └── kurage.yaml
└── docs/specs/web-app/         # 仕様書
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

---

## 技術スタック

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| FastAPI | ^0.115 | Web フレームワーク |
| Jinja2 | ^3.1 | テンプレートエンジン |
| HTMX | ^2.0 | 動的 UI 更新 |
| TailwindCSS | ^3.4 | スタイリング |
| SQLAlchemy | ^2.0 | ORM |
| Pydantic | ^2.0 | データバリデーション |
| sse-starlette | ^2.0 | Server-Sent Events |
| aiosqlite | ^0.20 | 非同期 SQLite ドライバ |
| python-multipart | ^0.0.9 | ファイルアップロード |

---

## ページ構成

### メインページ (`/`)

```
┌─────────────────────────────────────────┐
│           ヘッダー / ナビゲーション        │
│  [メイン] [履歴] [キャラクター]            │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │  キャラクター選択ドロップダウン     │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │     トピック入力エリア             │   │
│  │  "Transformerについて教えて"      │   │
│  │                                 │   │
│  │  [ファイルをドロップ]              │   │
│  └─────────────────────────────────┘   │
│         [生成する] ボタン               │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │     進捗表示エリア                 │   │
│  │  ● リサーチ中...                  │   │
│  │  ○ シナリオ作成                   │   │
│  │  ○ 画像生成                      │   │
│  └─────────────────────────────────┘   │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐   │
│  │     結果表示エリア                 │   │
│  │                                 │   │
│  │     [生成された画像]              │   │
│  │                                 │   │
│  │         [ダウンロード]            │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 履歴ページ (`/history`)

```
┌─────────────────────────────────────────┐
│           ヘッダー / ナビゲーション        │
├─────────────────────────────────────────┤
│  ┌───────┐ ┌───────┐ ┌───────┐         │
│  │ thumb │ │ thumb │ │ thumb │         │
│  │ 日時  │ │ 日時  │ │ 日時  │         │
│  │ トピック│ │ トピック│ │ トピック│         │
│  └───────┘ └───────┘ └───────┘         │
│  ┌───────┐ ┌───────┐ ┌───────┐         │
│  │ thumb │ │ thumb │ │ thumb │         │
│  │ 日時  │ │ 日時  │ │ 日時  │         │
│  │ トピック│ │ トピック│ │ トピック│         │
│  └───────┘ └───────┘ └───────┘         │
│                                         │
│        [もっと見る] ボタン               │
│        (hx-get="/api/history?page=2")   │
└─────────────────────────────────────────┘
```

### キャラクターカスタマイズページ (`/character`)

```
┌─────────────────────────────────────────┐
│           ヘッダー / ナビゲーション        │
├─────────────────────────────────────────┤
│  キャラクター一覧                         │
│  ┌───────┐ ┌───────┐ ┌───────┐         │
│  │[くらげ]│ │[新規+]│ │       │         │
│  └───────┘ └───────┘ └───────┘         │
├─────────────────────────────────────────┤
│  キャラクター編集                         │
│  ┌─────────────────────────────────┐   │
│  │  名前: [くらげ               ]   │   │
│  │  説明: [                     ]   │   │
│  │  外見: [ピンクの髪、大きな目...]   │   │
│  │  性格: [のんびり、好奇心旺盛...]   │   │
│  │  参照画像: [アップロード]         │   │
│  └─────────────────────────────────┘   │
│         [保存] [削除] ボタン             │
└─────────────────────────────────────────┘
```

---

## API エンドポイント

### ページルート（HTML レスポンス）

| Method | Path | 説明 |
|--------|------|------|
| GET | `/` | メインページ |
| GET | `/history` | 履歴ページ |
| GET | `/character` | キャラクターカスタマイズページ |

### API ルート（JSON/HTML パーシャル）

#### 生成 API

| Method | Path | 説明 | レスポンス |
|--------|------|------|-----------|
| POST | `/api/generate` | 生成開始 | JSON (`generation_id`) |
| GET | `/api/generate/{id}/stream` | SSE 進捗ストリーム | SSE |
| GET | `/api/generate/{id}/result` | 結果パーシャル | HTML |

#### 履歴 API

| Method | Path | 説明 | レスポンス |
|--------|------|------|-----------|
| GET | `/api/history` | 履歴一覧パーシャル | HTML |
| GET | `/api/history/{id}` | 履歴詳細 | JSON |
| DELETE | `/api/history/{id}` | 履歴削除 | HTML (empty) |

#### キャラクター API

| Method | Path | 説明 | レスポンス |
|--------|------|------|-----------|
| GET | `/api/characters` | キャラクター一覧 | JSON |
| GET | `/api/characters/{name}` | キャラクター詳細 | JSON |
| POST | `/api/characters` | キャラクター作成 | HTML |
| PUT | `/api/characters/{name}` | キャラクター更新 | HTML |
| DELETE | `/api/characters/{name}` | キャラクター削除 | HTML (empty) |

#### 画像 API

| Method | Path | 説明 | レスポンス |
|--------|------|------|-----------|
| GET | `/api/images/{id}` | 生成画像取得 | image/png |
| GET | `/api/images/{id}/thumbnail` | サムネイル取得 | image/png |
| GET | `/api/images/{id}/download` | ダウンロード | image/png (attachment) |

---

## HTMX パターン

### 生成リクエストフロー

```html
<!-- メインページのフォーム -->
<form hx-post="/api/generate"
      hx-target="#result-area"
      hx-swap="innerHTML"
      hx-indicator="#loading">
  <select name="character">
    <option value="kurage">くらげ</option>
  </select>
  <textarea name="topic" placeholder="トピックを入力..."></textarea>
  <button type="submit">生成する</button>
</form>

<!-- 進捗表示エリア（SSE で更新） -->
<div id="progress-area"
     hx-ext="sse"
     sse-connect="/api/generate/{id}/stream"
     sse-swap="message">
</div>

<!-- 結果表示エリア -->
<div id="result-area"></div>
```

### 履歴の無限スクロール

```html
<div id="history-list">
  {% for item in history %}
  <div class="history-item">...</div>
  {% endfor %}
  <button hx-get="/api/history?page={{ next_page }}"
          hx-target="#history-list"
          hx-swap="beforeend"
          hx-trigger="revealed">
    もっと見る
  </button>
</div>
```

---

## データベースモデル

```python
class GenerationHistory(Base):
    __tablename__ = "generation_history"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID
    character_name: Mapped[str] = mapped_column(String, nullable=False)
    input_topic: Mapped[str] = mapped_column(Text, nullable=False)
    generated_title: Mapped[str] = mapped_column(String, nullable=False)  # 3-5単語の要約
    image_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Character(Base):
    __tablename__ = "characters"

    name: Mapped[str] = mapped_column(String, primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    appearance: Mapped[str] = mapped_column(Text, nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    reference_image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

---

## データアクセス層

### Repository パターン

各モデルに対して Repository を作成し、データアクセスロジックをカプセル化：

```python
class BaseRepository[T]:
    """Generic base repository for common CRUD operations"""

    def __init__(self, session: AsyncSession, model_class: type[T]):
        self._session = session
        self._model_class = model_class

    async def get(self, id: str | int) -> T | None:
        """Get entity by primary key"""
        ...

    async def add(self, entity: T) -> T:
        """Add new entity"""
        ...

    async def delete(self, entity: T) -> None:
        """Delete entity"""
        ...


class GenerationRepository(BaseRepository[GenerationHistory]):
    """Repository for generation history data access"""

    async def get_by_id(self, generation_id: str) -> GenerationHistory | None:
        """Get generation by ID"""
        ...

    async def create(self, generation: GenerationHistory) -> GenerationHistory:
        """Create new generation record"""
        ...

    async def update_with_result(
        self, generation_id: str, image_data: bytes, title: str
    ) -> None:
        """Update generation with successful result"""
        ...

    async def update_error(self, generation_id: str, error_message: str) -> None:
        """Update generation with error status"""
        ...


class CharacterRepository(BaseRepository[Character]):
    """Repository for character data access"""

    async def get_by_name(self, name: str) -> Character | None:
        """Get character by name"""
        ...

    async def get_default(self) -> Character | None:
        """Get the default character"""
        ...

    async def list_all(self) -> list[Character]:
        """Get all characters"""
        ...
```

### DatabaseSession (Unit of Work)

トランザクション管理と複数 Repository の調整：

```python
class DatabaseSession:
    """
    Database session manager that coordinates repositories and transactions.
    Implements the Unit of Work pattern.
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self.generations = GenerationRepository(session)
        self.characters = CharacterRepository(session)

    async def commit(self) -> None:
        """Commit the current transaction"""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction"""
        await self._session.rollback()

    async def close(self) -> None:
        """Close the database session"""
        await self._session.close()
```

使用例（API レイヤ）：

```python
@router.post("/generate")
async def create_generation(
    topic: str = Form(...),
    character: str = Form(...),
    db_session: DatabaseSession = Depends(get_db_session),
):
    generation = GenerationHistory(...)
    await db_session.generations.create(generation)
    await db_session.commit()
    return {...}
```

---

## サービス層

### GeneratorService

```python
class GeneratorService:
    """Service for generating manga images with progress tracking"""

    async def generate_manga(
        self,
        generation_id: str,
        topic: str,
        character_name: str,
        db_session: DatabaseSession,
    ) -> AsyncGenerator[GenerationStatus, None]:
        """
        Generate manga image with SSE progress updates.

        Uses DatabaseSession to access repositories for data operations.
        """
        # Load character via repository
        character = await db_session.characters.get_by_name(character_name)

        # Generate manga using ManganizeAgent
        agent = ManganizeAgent(character=character)
        result = await agent.generate(topic)

        # Update database via repository
        await db_session.generations.update_with_result(
            generation_id, result.image_data, result.title
        )
        await db_session.commit()

        yield GenerationStatus(status="completed", ...)
```

---

## SSE（Server-Sent Events）フロー

```
Client                                    Server
   │                                         │
   │  POST /api/generate                     │
   │  {"topic": "...", "character": "..."}   │
   │ ───────────────────────────────────────►│
   │                                         │
   │  {"generation_id": "xxx"}               │
   │ ◄───────────────────────────────────────│
   │                                         │
   │  GET /api/generate/xxx/stream           │
   │  (hx-ext="sse" sse-connect)             │
   │ ───────────────────────────────────────►│
   │                                         │
   │  event: progress                        │
   │  data: <div>リサーチ中...</div>          │
   │ ◄───────────────────────────────────────│
   │                                         │
   │  event: progress                        │
   │  data: <div>シナリオ作成中...</div>      │
   │ ◄───────────────────────────────────────│
   │                                         │
   │  event: progress                        │
   │  data: <div>画像生成中...</div>          │
   │ ◄───────────────────────────────────────│
   │                                         │
   │  event: complete                        │
   │  data: <div hx-get="...">結果を表示</div>│
   │ ◄───────────────────────────────────────│
   │                                         │
```

**Note**: SSE レスポンスは HTML パーシャルを直接返し、HTMX がそのまま DOM にスワップする。

---

## TailwindCSS 設定

### tailwind.config.js

```javascript
module.exports = {
  content: [
    "./web/templates/**/*.html",
    "./web/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        // まんがタイムきらら風のパステルカラー
        kirara: {
          pink: '#FFB6C1',
          blue: '#87CEEB',
          yellow: '#FFFACD',
          green: '#98FB98',
        }
      },
      fontFamily: {
        // 日本語フォント
        sans: ['Noto Sans JP', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
```

### ビルドコマンド

```bash
# 開発時（ウォッチモード）
npx tailwindcss -i ./web/static/css/input.css -o ./web/static/css/output.css --watch

# 本番ビルド
npx tailwindcss -i ./web/static/css/input.css -o ./web/static/css/output.css --minify
```

---

## セキュリティ考慮事項

### 入力検証

- トピック長: 最大 10,000 文字
- ファイルサイズ: 最大 10MB
- ファイル形式: `.txt`, `.md` のみ
- キャラクター名: 英数字とアンダースコアのみ

### CSRF 対策

FastAPI の CSRF ミドルウェアを使用:

```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/api/generate")
async def generate(request: Request, csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    ...
```

### レート制限

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/generate")
@limiter.limit("10/minute")
async def generate(request: Request):
    ...
```

---

## デプロイメント

### 開発環境

```bash
# TailwindCSS ビルド（別ターミナル）
cd web && npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch

# FastAPI 起動
uv run uvicorn web.main:app --reload --port 8000
```

### 本番環境（将来）

- FastAPI: Docker コンテナ、Gunicorn + Uvicorn workers
- 静的ファイル: nginx または CDN で配信
- データベース: PostgreSQL（SQLite から移行）
- TailwindCSS: ビルド済み CSS をコンテナに含める
