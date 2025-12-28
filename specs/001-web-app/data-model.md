# Data Model: Manganize Web App

**Created**: 2025-12-27
**Purpose**: データベーススキーマとエンティティ定義

## エンティティ概要

| エンティティ | 説明 | 主キー |
|-------------|------|-------|
| GenerationHistory | マンガ生成履歴 | id (UUID) |
| Character | カスタムキャラクター定義 | name (文字列) |

## GenerationHistory

マンガ画像の生成リクエストとその結果を保存する。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|-------------|---|------|------|
| id | String (UUID) | PRIMARY KEY, NOT NULL | 生成リクエストの一意識別子 |
| character_name | String(100) | NOT NULL, FK → Character.name | 使用したキャラクター |
| input_topic | Text | NOT NULL | ユーザーが入力したトピック |
| generated_title | String(100) | NOT NULL | LLM生成の短いタイトル（3-5単語） |
| image_data | LargeBinary | NULLABLE | 生成されたPNG画像のバイナリデータ |
| status | String(20) | NOT NULL, DEFAULT 'pending' | 生成状態: pending, researching, writing, generating, completed, error |
| error_message | Text | NULLABLE | エラーメッセージ（status='error'の場合） |
| created_at | DateTime | NOT NULL, DEFAULT now() | 生成リクエスト作成日時 |
| completed_at | DateTime | NULLABLE | 生成完了日時 |

### インデックス

- `idx_created_at` ON `created_at` DESC（履歴一覧の高速化）
- `idx_status` ON `status`（未完了の生成を検索）

### バリデーションルール

- `input_topic`: 1〜10,000 文字
- `generated_title`: 1〜100 文字
- `status`: 列挙型 (pending, researching, writing, generating, completed, error)
- `character_name`: Character テーブルに存在する名前

### 状態遷移

```
pending → researching → writing → generating → completed
   ↓
 error (任意の状態から遷移可能)
```

### SQLAlchemy モデル

```python
from datetime import datetime
from sqlalchemy import String, Text, LargeBinary, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class GenerationHistory(Base):
    __tablename__ = "generation_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    character_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_topic: Mapped[str] = mapped_column(Text, nullable=False)
    generated_title: Mapped[str] = mapped_column(String(100), nullable=False)
    image_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_created_at", "created_at", postgresql_using="btree"),
        Index("idx_status", "status"),
    )
```

## Character

カスタムキャラクターの定義を保存する。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|-------------|---|------|------|
| name | String(100) | PRIMARY KEY, NOT NULL | キャラクター名（一意、英数字とアンダースコアのみ） |
| display_name | String(200) | NOT NULL | 表示名（日本語可） |
| nickname | String(200) | NULLABLE | ニックネーム |
| attributes | JSON | NOT NULL | 属性リスト（例: ["ハイスキルエンジニア", "技術オタク"]） |
| personality | Text | NOT NULL | 性格の基本説明 |
| speech_style | JSON | NOT NULL | 話し方スタイル（tone, patterns, examples, forbidden） |
| reference_images | JSON | NULLABLE | 参照画像のパス（portrait, full_body を含む JSON） |
| is_default | Boolean | NOT NULL, DEFAULT false | デフォルトキャラクターフラグ |
| created_at | DateTime | NOT NULL, DEFAULT now() | 作成日時 |
| updated_at | DateTime | NOT NULL, DEFAULT now() | 更新日時 |

### インデックス

- `idx_name` ON `name`（主キーなので自動作成）

### バリデーションルール

- `name`: 1〜100 文字, 英数字とアンダースコアのみ (`^[a-zA-Z0-9_]+$`)
- `display_name`: 1〜200 文字
- `nickname`: 0〜200 文字（任意）
- `attributes`: JSON 配列、各要素は 1〜100 文字
- `personality`: 1〜2,000 文字
- `speech_style`: JSON オブジェクト、必須キー: tone, patterns, examples, forbidden
- `reference_images`: JSON オブジェクト（任意）、キー: portrait, full_body、値: 画像パス文字列
- `is_default`: デフォルトキャラクター（"kurage"）は削除不可

### 初期データ

```yaml
# characters/kurage/kurage.yaml から読み込み
name: kurage
display_name: くらがりくらげ
nickname: くらげちゃん
attributes: ["ハイスキルエンジニア", "技術オタク"]
personality: 基本はクールでダウナーだが、技術的な話題には目を輝かせます。
speech_style:
  tone: 声のトーンが低めの、落ち着いた現代の女の子
  patterns: ["～かも", "～だね", "……なるほど", "～らしいよ"]
  examples: ["これ、結構面白いかも", "なるほどね……", "そういうことだったんだ"]
  forbidden: ["「～だ」「～である」等の堅苦しい断定", "おじさん構文", "博士語調（～じゃ、～わい）", "過度にハイテンションなアイドル口調"]
reference_images:
  portrait: "characters/kurage/assets/kurage.png"
  full_body: "characters/kurage/assets/kurage2.png"
is_default: true
```

### SQLAlchemy モデル

```python
from datetime import datetime
from typing import Any
from sqlalchemy import String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Character(Base):
    __tablename__ = "characters"

    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(200), nullable=True)
    attributes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    speech_style: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    reference_images: Mapped[dict[str, str] | None] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## リレーション

### GenerationHistory → Character

- **関係**: Many-to-One
- **外部キー**: `GenerationHistory.character_name` → `Character.name`
- **カスケード**: RESTRICT（キャラクターを削除する前に関連する履歴を削除する必要がある）
- **理由**: 履歴からキャラクター名を参照して再現できるようにする

## Pydantic スキーマ

### GenerationCreate (リクエスト)

```python
from pydantic import BaseModel, Field

class GenerationCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=10000)
    character: str = Field(..., min_length=1, max_length=100)
```

### GenerationResponse (レスポンス)

```python
from pydantic import BaseModel
from datetime import datetime

class GenerationResponse(BaseModel):
    id: str
    character_name: str
    input_topic: str
    generated_title: str
    status: str
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
```

### CharacterCreate (リクエスト)

```python
from pydantic import BaseModel, Field

class SpeechStyle(BaseModel):
    tone: str
    patterns: list[str]
    examples: list[str]
    forbidden: list[str]

class ReferenceImages(BaseModel):
    portrait: str | None = None
    full_body: str | None = None

class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str = Field(..., min_length=1, max_length=200)
    nickname: str | None = Field(None, max_length=200)
    attributes: list[str] = Field(default_factory=list)
    personality: str = Field(..., min_length=1, max_length=2000)
    speech_style: SpeechStyle
    reference_images: ReferenceImages | None = None
```

### CharacterResponse (レスポンス)

```python
from pydantic import BaseModel
from datetime import datetime

class CharacterResponse(BaseModel):
    name: str
    display_name: str
    nickname: str | None
    attributes: list[str]
    personality: str
    speech_style: dict[str, any]
    reference_images: dict[str, str] | None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## マイグレーション

### Alembic 使用

SQLAlchemy + Alembic でマイグレーション管理：

```bash
# 初期化
alembic init alembic

# マイグレーション生成
alembic revision --autogenerate -m "Create generation_history and characters tables"

# マイグレーション実行
alembic upgrade head
```

### 初期データ投入

```python
# web/models/seed.py
import yaml
from pathlib import Path

async def seed_default_character(session: AsyncSession):
    kurage_file = Path("characters/kurage/kurage.yaml")
    with open(kurage_file) as f:
        data = yaml.safe_load(f)

    character = Character(
        name=data["name"],
        description=data["description"],
        appearance=data["appearance"],
        personality=data["personality"],
        is_default=True
    )

    session.add(character)
    await session.commit()
```

## データベース接続設定

### Development (SQLite)

```python
# web/config.py
DATABASE_URL = "sqlite+aiosqlite:///./manganize.db"
```

### Production (PostgreSQL)

```python
# web/config.py
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/manganize")
```

## ストレージ考慮事項

### 画像ストレージ

- **開発**: データベースに BLOB として保存（SQLite の制限: 1GB/ファイル）
- **本番**: S3 や Cloud Storage への移行を検討（URL のみを DB に保存）

### 履歴保持

- 初期バージョンでは無期限保持
- 将来的に自動削除ポリシーを追加する可能性（例: 90日以上前のものを削除）
