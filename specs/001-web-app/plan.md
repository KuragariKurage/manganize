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
├── api/                 # API routes
│   ├── __init__.py
│   ├── generation.py    # POST /api/generate, GET /api/generate/{id}/stream, etc.
│   ├── character.py     # CRUD for characters
│   └── history.py       # GET /api/history, DELETE /api/history/{id}
├── models/              # Database models (SQLAlchemy)
│   ├── __init__.py
│   ├── database.py      # DB connection setup
│   ├── generation.py    # GenerationHistory model
│   └── character.py     # Character model
├── schemas/             # Pydantic schemas for validation
│   ├── __init__.py
│   ├── generation.py    # GenerationCreate, GenerationResponse
│   └── character.py     # CharacterCreate, CharacterUpdate
├── services/            # Business logic layer
│   ├── __init__.py
│   ├── generator.py     # Wraps ManganizeAgent, handles SSE progress
│   ├── character.py     # Character CRUD logic
│   └── history.py       # History retrieval and management
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

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

該当なし - すべての原則に準拠
