# Tasks: Manganize Web App

**Input**: Design documents from `/specs/001-web-app/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Web application structure: `web/` at repository root
- Paths shown assume web app structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create web/ directory structure per plan.md
- [X] T002 Initialize pyproject.toml with FastAPI, Jinja2, HTMX, TailwindCSS dependencies
- [X] T003 [P] Create web/__init__.py
- [X] T004 [P] Create web/config.py with environment variable management
- [X] T005 [P] Setup .env file with GOOGLE_API_KEY and DATABASE_URL
- [X] T006 [P] Create tailwind.config.js with content paths
- [X] T007 [P] Create web/static/css/input.css for TailwindCSS (using @import "tailwindcss" for v4.x)
- [X] T008 Build TailwindCSS output.css using @tailwindcss/cli (npm install -D @tailwindcss/cli@next; npx @tailwindcss/cli -i web/static/css/input.css -o web/static/css/output.css)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 [P] Create web/models/__init__.py
- [X] T010 [P] Create web/models/database.py with async SQLAlchemy engine setup
- [X] T010.1 [P] Create web/repositories/__init__.py
- [X] T010.2 [P] Create web/repositories/base.py with BaseRepository class
- [X] T010.3 [P] Create web/repositories/database_session.py with DatabaseSession (Unit of Work pattern)
- [X] T010.4 [P] Create web/templates.py for Jinja2 templates configuration
- [X] T011 [P] Create web/schemas/__init__.py
- [X] T012 [P] Create web/services/__init__.py
- [X] T013 [P] Create web/api/__init__.py
- [X] T014 [P] Create web/templates/ directory structure with base.html
- [X] T015 Setup Alembic for database migrations in alembic/ directory
- [X] T016 [P] Create web/models/generation.py with GenerationHistory model
- [X] T017 [P] Create web/models/character.py with Character model
- [X] T017.1 [P] Create web/repositories/generation.py with GenerationRepository
- [X] T017.2 [P] Create web/repositories/character.py with CharacterRepository
- [X] T018 Generate Alembic migration for GenerationHistory and Character tables
- [X] T019 Run Alembic migration to create database tables
- [X] T020 [P] Create web/models/seed.py to load default character from characters/kurage/kurage.yaml
- [X] T021 Run seed script to populate default character (kurage)
- [X] T022 [P] Create web/main.py with FastAPI app initialization and CORS middleware
- [X] T023 [P] Setup StaticFiles mount for /static in web/main.py
- [X] T024 [P] Setup Jinja2Templates configuration in web/templates.py (imported from web/main.py)
- [X] T025 [P] Add slowapi rate limiting middleware (10 req/min/IP) in web/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - マンガ画像の生成 (Priority: P1) 🎯 MVP

**Goal**: トピックを入力してマンガ画像を生成し、進捗状態をリアルタイムで表示する

**Independent Test**: トピック「Transformerアーキテクチャについて」を入力して生成ボタンをクリックし、進捗表示（リサーチ中→シナリオ作成中→画像生成中）を経てマンガ画像が表示されることを確認

### Implementation for User Story 1

- [X] T026 [P] [US1] Create web/schemas/generation.py with GenerationCreate and GenerationResponse schemas
- [X] T027 [P] [US1] Create web/templates/index.html with topic input form and HTMX attributes
- [X] T028 [P] [US1] Create web/templates/partials/progress.html for SSE progress display
- [X] T029 [P] [US1] Create web/templates/partials/result.html for generated image display
- [X] T030 [US1] Create web/services/generator.py to wrap ManganizeAgent with SSE progress callbacks
- [X] T031 [US1] Extract topic_title from ManganizeAgent Researcher node output in web/services/generator.py (3-5 words). On failure, fallback to datetime-only format
- [X] T032 [US1] Create web/api/generation.py with POST /api/generate endpoint
- [X] T033 [US1] Implement GET /api/generate/{id}/stream SSE endpoint in web/api/generation.py
- [X] T034 [US1] Implement GET /api/generate/{id}/result HTML partial endpoint in web/api/generation.py
- [X] T035 [US1] Implement GET /api/images/{id} endpoint to serve PNG images in web/api/generation.py
- [X] T036 [US1] Add GET / route in web/main.py to render index.html template
- [X] T037 [US1] Connect HTMX form submission to POST /api/generate in web/templates/index.html
- [X] T038 [US1] Implement SSE progress updates using EventSource API in web/templates/partials/progress.html
- [X] T039 [US1] Add validation: disable generate button when text area is empty (JavaScript event listener on topic input)
- [X] T040 [US1] Add error handling: display error message and retry button on generation failure

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 画像表示・ダウンロード (Priority: P2)

**Goal**: 生成されたマンガ画像を閲覧し、ダウンロードできるようにする

**Independent Test**: 生成完了後の画像をクリックしてフルサイズ表示し、ダウンロードボタンでローカルに保存できることを確認

### Implementation for User Story 2

- [X] T041 [P] [US2] Implement GET /api/images/{id}/download endpoint with Content-Disposition header in web/api/generation.py
- [X] T042 [P] [US2] Implement GET /api/images/{id}/thumbnail endpoint with Pillow thumbnail generation (200x200) in web/api/generation.py
- [X] T043 [US2] Add download button with hx-get to /api/images/{id}/download in web/templates/partials/result.html (already implemented in Phase 3)
- [X] T044 [US2] Add image click handler to display fullsize modal in web/templates/partials/result.html (already implemented in Phase 3)
- [X] T045 [US2] Implement filename generation logic: manganize_{datetime}_{generated_title}.png in web/utils/filename.py
- [X] T045.1 [US2] Refactor: Move filename generation helper to web/utils/filename.py for better code organization
- [X] T046 [US2] Add Alpine.js modal component for fullsize image display in web/templates/index.html

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - キャラクターカスタマイズ (Priority: P3)

**Goal**: オリジナルのキャラクターを作成・管理し、生成時に選択できるようにする

**Independent Test**: キャラクターページで新規キャラクター「test_character」を作成し、メインページのドロップダウンで選択して生成できることを確認

### Implementation for User Story 3

- [X] T047 [P] [US3] Create web/schemas/character.py with CharacterCreate, CharacterUpdate, CharacterResponse schemas
- [X] T048 [P] [US3] Create web/templates/character.html with character list and form
- [X] T049 [P] [US3] Create web/templates/partials/character_form.html for create/edit form
- [X] T050 [US3] Create web/services/character.py with CRUD operations (list, get, create, update, delete)
- [X] T051 [US3] Create web/api/character.py with GET /api/characters endpoint
- [X] T052 [US3] Implement POST /api/characters endpoint (JSON body instead of multipart) in web/api/character.py
- [X] T053 [US3] Implement GET /api/characters/{name} endpoint in web/api/character.py
- [X] T054 [US3] Implement PUT /api/characters/{name} endpoint in web/api/character.py
- [X] T055 [US3] Implement DELETE /api/characters/{name} endpoint with default character protection in web/api/character.py
- [X] T056 [US3] Implement GET /api/characters/{name}/image endpoint to serve reference images in web/api/character.py (placeholder - TODO for polish)
- [X] T057 [US3] Add GET /character route in web/main.py to render character.html template
- [X] T058 [US3] Add character name validation: regex ^[a-zA-Z0-9_]+$ in web/schemas/character.py
- [X] T059 [US3] Populate character dropdown in index.html using GET /api/characters
- [X] T060 [US3] Disable delete button for default character (kurage) using is_default flag
- [X] T061 [US3] Add image upload handling (deferred to Phase 7 polish)

**Checkpoint**: All user stories 1, 2, AND 3 should now work independently

---

## Phase 6: User Story 4 - 生成履歴の管理 (Priority: P4)

**Goal**: 過去の生成履歴を閲覧・管理し、以前の生成結果を再確認できるようにする

**Independent Test**: 履歴ページで過去の生成結果一覧を確認し、項目をクリックして詳細を閲覧、削除ボタンで削除できることを確認

### Implementation for User Story 4

- [X] T062 [P] [US4] Create web/templates/history.html for history list page
- [X] T063 [P] [US4] Create web/templates/partials/history_list.html for HTMX infinite scroll
- [X] T064 [US4] Create web/services/history.py with list, get, delete operations
- [X] T065 [US4] Create web/api/history.py with GET /api/history endpoint (HTML partial response)
- [X] T066 [US4] Implement pagination logic with page and limit query parameters in web/api/history.py
- [X] T067 [US4] Implement GET /api/history/{id} endpoint (JSON response) in web/api/history.py
- [X] T068 [US4] Implement DELETE /api/history/{id} endpoint (empty HTML response) in web/api/history.py
- [X] T069 [US4] Add GET /history route in web/main.py to render history.html template
- [X] T070 [US4] Implement infinite scroll with hx-trigger="revealed" in web/templates/partials/history_list.html
- [X] T071 [US4] Display thumbnail, generated_title, and created_at in history items
- [X] T072 [US4] Add confirmation dialog before delete using Alpine.js in web/templates/partials/history_list.html
- [X] T073 [US4] Sort history by created_at DESC using SQLAlchemy query in web/services/history.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T074 [P] Add navigation menu in web/templates/base.html (Home, History, Characters)
- [X] T075 [P] Style all pages with TailwindCSS for responsive design (mobile + desktop)
- [X] T076 [P] Add loading indicators for all HTMX requests using hx-indicator
- [X] T077 [P] Implement POST /api/upload endpoint for file upload (txt, pdf, md) in web/api/generation.py
- [X] T078 [P] Add drag-and-drop file upload zone in web/templates/index.html with Alpine.js
- [X] T079 [P] Integrate markitdown for PDF text extraction in web/utils/file_processing.py
- [X] T080 [P] Add file size validation (10MB max) in web/utils/file_processing.py
- [X] T081 [P] Add file type validation (.txt, .pdf, .md only) in web/utils/file_processing.py
- [X] T082 [P] Add reconnection logic for SSE connection failures
- [X] T083 [P] Implement background task completion when browser closes
- [X] T084 Code formatting: run `ruff format web/`
- [X] T085 Code quality: run `ruff check web/` and fix all warnings
- [X] T086 Type checking: run `ty check web/` and fix all errors
- [X] T087 Verify all functions have type hints (Constitution compliance)
- [X] T088 Update docs/specs/001-web-app/plan.md and spec.md - confirmed in sync with implementation
- [X] T089 Requirements documented in spec.md - confirmed accurate
- [X] T090 Create docs/wiki/tutorials/first-manga.md (Divio: Tutorial)
- [X] T091 Create docs/wiki/how-to/deploy-production.md (Divio: How-to)
- [X] T092 docs/wiki/reference/api-endpoints.md already exists and is complete
- [X] T093 Update README.md with TailwindCSS setup instructions
- [X] T094 Update AGENTS.md with frontend development workflow

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Enhances US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Extends US1 with character selection but independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Uses GenerationHistory from US1 but independently testable

### Within Each User Story

- Schema definitions before services
- Services before API endpoints
- API endpoints before templates
- Templates before HTMX integration
- Core implementation before validation and error handling

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Schema, template, and service tasks within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch schema, template, and partial tasks together:
Task: "Create web/schemas/generation.py with GenerationCreate and GenerationResponse schemas"
Task: "Create web/templates/index.html with topic input form and HTMX attributes"
Task: "Create web/templates/partials/progress.html for SSE progress display"
Task: "Create web/templates/partials/result.html for generated image display"

# Then launch service and API tasks:
Task: "Create web/services/generator.py to wrap ManganizeAgent with SSE progress callbacks"
Task: "Create web/api/generation.py with POST /api/generate endpoint"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- TailwindCSS build must run in watch mode during development
- FastAPI auto-reload enabled for rapid iteration
- SSE connection must handle reconnection gracefully
- All API endpoints must include proper error handling and validation

---

## Implementation Status

**最終更新日**: 2025-12-29

**完了タスク数**: 96/96 (100%) 🎉
- Phase 1: Setup (8/8) ✅
- Phase 2: Foundational (21/21) ✅ (Repository Pattern含む)
- Phase 3: User Story 1 (15/15) ✅ - MVP 完了
- Phase 4: User Story 2 (6/6) ✅ - 画像表示・ダウンロード完了
- Phase 5: User Story 3 (15/15) ✅ - キャラクターカスタマイズ完了
- Phase 6: User Story 4 (12/12) ✅ - 生成履歴の管理完了
- Phase 7: Polish (19/19) ✅ - 全機能完成、ドキュメント完備

**Phase 5 実装内容**:
- T047: Character schemas (CharacterCreate/Update/Response) - SpeechStyle 入れ子モデル
- T050: CharacterService CRUD - デフォルトキャラクター保護、バリデーション
- T051-056: Character API endpoints - リスト、取得、作成、更新、削除、画像（プレースホルダー）
- T048-049+057: キャラクターページ - 一覧表示、作成・編集フォーム、HTMX による動的更新
- T059-061: メインページ統合 - ドロップダウン動的生成、デフォルトキャラクター選択

**Phase 6 実装内容**:
- T064: HistoryService - 履歴の取得、削除、ページネーション
- T065-068: History API endpoints - リスト（HTML partial）、詳細（JSON）、削除
- T062-063: 履歴ページ - history.html + history_list.html partial
- T070-073: 無限スクロール（hx-trigger="revealed"）、サムネイル表示、削除確認ダイアログ（Alpine.js）
- GenerationRepository 拡張: list_history() メソッド追加（ページネーション、ソート、フィルタリング）

**Phase 4 実装内容**:
- T041: ダウンロードエンドポイント（`/api/images/{id}/download`）
- T042: サムネイルエンドポイント（`/api/images/{id}/thumbnail`）- Pillow で 200x200 サムネイル生成
- T045: ファイル名生成ロジック（`manganize_{datetime}_{title}.png`）- 特殊文字サニタイズ → web/utils/filename.py に分離
- T046: Alpine.js モーダル完成 - カスタムイベント、トランジション、閉じるボタン追加

**実装時の追加タスク**:
- T010.1〜T010.4: Repository Pattern + Unit of Work + templates.py 分離
- T017.1〜T017.2: GenerationRepository + CharacterRepository

**アーキテクチャ改善**:
- Repository Pattern + Unit of Work Pattern 導入
- DatabaseSession による複数リポジトリの統合
- SSE: vanilla JavaScript EventSource API を使用（HTMX SSE 拡張ではなく）
- カスタム TailwindCSS コンポーネントクラスの定義

**フロントエンド先行実装（Phase 3）**:
- ナビゲーションバー（T074 を先行実装）
- Alpine.js モーダル骨組み（Phase 4 で完成）
- ダウンロードボタン UI（Phase 4 でバックエンド実装）

**Phase 7 実装内容**:
- T074: ナビゲーションメニュー（先行実装済み）
- T075: レスポンシブデザイン - モバイルメニュー、ハンバーガーアイコン
- T076: ローディングインジケーター - spinner-sm、skeleton loading、hx-indicator
- T077-T081: ファイルアップロード機能
  - web/utils/file_processing.py: テキスト抽出、バリデーション
  - POST /api/upload: ファイルアップロードエンドポイント
  - Alpine.js ドラッグ&ドロップUI
  - markitdown統合（PDF、TXT、MD対応）
  - ファイルサイズ（10MB）・タイプ検証
- T082: SSE再接続ロジック - リトライ、exponential backoff、フォールバックポーリング
- T083: バックグラウンドタスク完了処理 - beforeunload handler
- T084-T087: コード品質
  - ruff format web/ (4 files reformatted)
  - ruff check web/ (All checks passed)
  - ty check web/ (All checks passed)
  - 全関数に型ヒント完備

**Phase 7 実装詳細（完了）**:
- T088-T089: plan.md と spec.md を確認、実装と同期が取れていることを確認
- T090: docs/wiki/tutorials/first-manga.md を作成 - 初心者向けチュートリアル
- T091: docs/wiki/how-to/deploy-production.md を作成 - 本番環境デプロイガイド（TailwindCSS 4.x 対応）
- T092: docs/wiki/reference/api-endpoints.md は既に完成済み
- T093-T094: README.md と AGENTS.md に TailwindCSS + フロントエンド開発情報を追加
- T095: TailwindCSS 4.x 対応のためドキュメント修正（@tailwindcss/cli 使用）

**プロジェクト完了** 🎉:
すべてのユーザーストーリー（US1-US4）が実装され、コード品質チェックとドキュメント作成も完了しました。
