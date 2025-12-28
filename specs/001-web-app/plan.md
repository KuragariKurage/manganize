# Implementation Plan: Manganize Web App

**Branch**: `001-web-app` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-web-app/spec.md`

## Summary

既存の manganize コアエージェント（LangGraph ベース）を Web アプリケーションとしてユーザーに提供する。HTMX + FastAPI + TailwindCSS + Jinja2 スタックでサーバーサイドレンダリングを基本とし、SSE でリアルタイム進捗通知を実現する。主要機能は、トピック入力→マンガ画像生成→画像表示・ダウンロード、キャラクターカスタマイズ、生成履歴管理。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastAPI ^0.115, Jinja2 ^3.1, HTMX ^2.0, TailwindCSS ^3.4, sse-starlette ^2.0
**Storage**: SQLite (開発環境), PostgreSQL (本番環境への移行可能性あり)
**Testing**: pytest (バックエンド), HTMX による統合テスト (フロントエンド)
**Target Platform**: Linux server (開発時は WSL2), ブラウザ (Chrome, Firefox, Safari 最新版)
**Project Type**: Web application (FastAPI backend + HTMX/Jinja2 frontend)
**Performance Goals**: ページ初期表示 < 2秒, 進捗更新 < 1秒, 履歴追加読み込み < 1秒
**Constraints**: 同時生成は 1 ユーザーあたり 1 プロセス, ファイルアップロード上限 10MB, 認証なし (ローカル使用想定)
**Scale/Scope**: 個人使用想定, ~100 生成履歴, 3-5 カスタムキャラクター

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with [Constitution](../../.specify/memory/constitution.md):

- [x] **Spec駆動開発**: Feature has corresponding spec files (spec.md ✓, requirements.md ✓, design.md ✓)
- [x] **型安全性**: Plan includes type checking strategy (`ty check` on all Python code)
- [x] **EARS記法準拠**: Requirements in spec.md follow EARS patterns (FR-001~FR-017 verified)
- [x] **Divioドキュメンテーション**: Documentation will be placed in `docs/wiki/` following 4-quadrant system
- [x] **コード品質**: Plan includes `ruff check` and `ruff format` quality gates
- [ ] **LangGraphベース設計**: Partially applicable - uses existing manganize core agent (LangGraph), web layer wraps it
- [x] **Webアプリケーションスタック**: Uses HTMX + FastAPI + TailwindCSS + Jinja2 stack as mandated

**Complexity Justification Required**: None - all principles are followed

## Project Structure

### Documentation (this feature)

```text
specs/001-web-app/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
│   ├── generation-api.yaml
│   ├── character-api.yaml
│   └── history-api.yaml
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
web/                     # Web application root
├── __init__.py
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management (env vars, settings)
├── templates.py         # Jinja2 templates configuration
├── api/                 # API routes
│   ├── __init__.py
│   ├── generation.py    # POST /api/generate, GET /api/generate/{id}/stream, etc.
│   ├── character.py     # CRUD for characters
│   └── history.py       # GET /api/history, DELETE /api/history/{id}
├── models/              # Database models (SQLAlchemy)
│   ├── __init__.py
│   ├── database.py      # DB connection setup
│   ├── generation.py    # GenerationHistory model
│   ├── character.py     # Character model
│   └── seed.py          # Database seeding (default character)
├── repositories/        # Repository pattern (data access layer)
│   ├── __init__.py
│   ├── base.py          # Base repository class
│   ├── database_session.py  # DatabaseSession (Unit of Work pattern)
│   ├── generation.py    # GenerationRepository
│   └── character.py     # CharacterRepository
├── schemas/             # Pydantic schemas for validation
│   ├── __init__.py
│   ├── generation.py    # GenerationCreate, GenerationResponse
│   └── character.py     # CharacterCreate, CharacterUpdate
├── services/            # Business logic layer
│   ├── __init__.py
│   ├── generator.py     # Wraps ManganizeAgent, handles SSE progress
│   ├── character.py     # Character CRUD logic
│   └── history.py       # History retrieval and management
├── utils/               # Utility functions
│   ├── __init__.py
│   └── filename.py      # Filename generation utilities
├── templates/           # Jinja2 templates
│   ├── base.html        # Base layout with TailwindCSS
│   ├── index.html       # Main page (topic input + generation)
│   ├── history.html     # History list page
│   ├── character.html   # Character customization page
│   └── partials/        # HTMX partial templates
│       ├── progress.html       # Progress indicator
│       ├── result.html         # Generated image display
│       ├── history_list.html   # History items
│       └── character_form.html # Character form
└── static/              # Static assets
    ├── css/
    │   ├── input.css    # TailwindCSS input
    │   └── output.css   # TailwindCSS compiled output
    ├── js/
    │   └── htmx.min.js  # HTMX library (CDN fallback)
    └── images/          # UI images, icons

tests/                   # Test suite
├── conftest.py          # Pytest fixtures
├── test_api/            # API endpoint tests
│   ├── test_generation.py
│   ├── test_character.py
│   └── test_history.py
├── test_services/       # Service layer unit tests
│   ├── test_generator.py
│   └── test_character.py
└── test_models/         # Database model tests
    └── test_history.py

manganize/               # Existing core agent (unchanged)
├── agents.py
├── prompts.py
└── tools.py

characters/              # Character definitions
└── kurage/
    └── kurage.yaml

pyproject.toml           # Updated with web dependencies
uv.lock                  # Updated lock file
```

**Structure Decision**: Web application structure (Option 2 variant). FastAPI backend と Jinja2/HTMX frontend を統合した単一プロジェクト構成。既存の `manganize/` コアエージェントはそのまま保持し、`web/` ディレクトリで FastAPI アプリケーションを新規構築。サーバーサイドレンダリング（SSR）を基本とし、HTMX で動的な UI 更新を実現。

**Architecture Patterns** (実装時に追加):
- **Repository Pattern**: データアクセスロジックを `repositories/` に分離。モデル層とサービス層の疎結合を実現。
- **Unit of Work Pattern**: `DatabaseSession` クラスで複数リポジトリのトランザクション管理を統合。commit/rollback の制御を一元化。
- **Dependency Injection**: FastAPI の `Depends` を使用して、各エンドポイントに `DatabaseSession` を注入。テスト容易性とコードの可読性を向上。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

該当なし - すべての原則に準拠

## Implementation Notes

**Phase 3 (MVP) 完了時の追加実装**:

以下のアーキテクチャパターンが実装時に追加されました（Phase 2 Foundational で導入）：

1. **Repository Pattern + Unit of Work Pattern**
   - データアクセスロジックを `web/repositories/` に分離
   - `DatabaseSession` クラスで複数リポジトリのトランザクション管理を統合
   - サービス層からモデル層への直接アクセスを排除し、保守性を向上
   - 理由: 将来的なデータベース変更やテストの容易性を考慮

2. **templates.py の分離**
   - Jinja2 テンプレート設定を `web/templates.py` に分離
   - main.py の肥大化を防止
   - 理由: 設定の一元管理と可読性向上

3. **タイトル生成の実装詳細**
   - ManganizeAgent の Researcher ノードが `topic_title` を生成（3-5単語）
   - generator.py はそれを受け取り、生成失敗時は `datetime.now().strftime("%Y%m%d_%H%M%S")` をフォールバックとして使用
   - 実装: `web/services/generator.py` L170-172
   - 仕様準拠: spec.md Assumptions L138

4. **SSE 実装方法**
   - HTMX の `hx-ext="sse"` ではなく、vanilla JavaScript の `EventSource` API を使用
   - 理由: より細かい制御が必要（進捗バーの色変更、完了時の自動リロード等）
   - 実装: `web/templates/partials/progress.html` L29-83
   - HTMX との統合: 完了時に `htmx.ajax()` を使用して結果を動的にロード（L64-67）

**変更の影響範囲**:
- tasks.md: T010.1～T010.4, T017.1～T017.2, T024, T031 を追加・更新
- plan.md: Project Structure と Architecture Patterns セクションを更新
- spec.md: 変更なし（実装は仕様に準拠）

**フロントエンドの先行実装** (Phase 3):
以下の UI 要素が Phase 3 (MVP) で実装済みで、Phase 4 でバックエンドや機能が完成：

- **ナビゲーション**: `web/templates/base.html` L22-33 にナビゲーションバーを実装済み（T074 を先行実装）
  - 履歴ページ、キャラクターページへのリンクは Phase 5, 6 で機能化予定
- **Alpine.js 導入**: `web/templates/base.html` L16 で Alpine.js を CDN から読み込み済み
  - Phase 4 のモーダル機能（T046）で本格利用 ✅
- **モーダル骨組み**: `web/templates/index.html` L70-84 に Alpine.js モーダルを追加済み → Phase 4 で完成 ✅
- **ダウンロードリンク**: `web/templates/partials/result.html` L23-27 にダウンロードボタンを追加済み → Phase 4 で完成 ✅
- **カスタム TailwindCSS コンポーネント**: `web/static/css/input.css` に再利用可能なコンポーネントクラスを定義
  - `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.card`, `.input-field`, `.textarea-field`
  - HTMX インジケーター用のユーティリティクラス（L90-100）

**Phase 4 実装詳細** (2025-12-28 完了):

1. **ダウンロード機能**:
   - `GET /api/images/{id}/download` エンドポイント追加
   - ファイル名生成: `manganize_{YYYYMMDD_HHMMSS}_{sanitized_title}.png`
   - 特殊文字サニタイズ: 非英数字を `_` に置換、最大50文字にトリミング
   - `Content-Disposition: attachment` ヘッダーでダウンロードを強制
   - **リファクタリング**: ファイル名生成ロジックを `web/utils/filename.py` に分離（ルーターの可読性向上）

2. **サムネイル生成**:
   - `GET /api/images/{id}/thumbnail` エンドポイント追加
   - Pillow で 200x200 サムネイルを生成（アスペクト比維持、LANCZOS リサンプリング）
   - Phase 6 の履歴一覧で使用予定

3. **Alpine.js モーダル**:
   - カスタムイベント (`@open-modal.window`) でモーダルを開く
   - トランジション効果追加（フェードイン/アウト、スケール）
   - 閉じるボタン（×）、ESC キー、背景クリックでクローズ
   - `x-cloak` でちらつき防止

4. **コード品質改善**:
   - `web/utils/` ディレクトリ新設
   - ヘルパー関数を utils に分離し、API ルーターのコードを簡潔に保つ
   - ファイル名生成ユーティリティに docstring と使用例を追加

**次フェーズへの引き継ぎ事項**:
- Repository Pattern は Phase 5～7 でも継続使用
- Character と History の Repository は Phase 5, 6 で拡張予定
- サムネイルエンドポイント（T042）は Phase 6 の履歴一覧で活用予定
