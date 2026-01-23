# Feature Specification: AgentCore Runtime 分離

**Feature Branch**: `claude/agent-runtime-separation-c3YES`
**Created**: 2025-01-23
**Status**: Draft
**Input**: エージェント動作部分を別サービス（AgentCore Runtime）として切り離し、リソース分離を実現する

## 背景と目的

現在、`ManganizeAgent`（LangGraph）は Web アプリケーションと同一プロセスで動作している。
エージェント処理は CPU/メモリ負荷が高く、Web サーバーのレスポンス性能に影響を与える可能性がある。

**目的**: リソース分離により、エージェント処理と Web サーバーを独立してスケーリング・運用可能にする。

## User Scenarios & Testing

### User Story 1 - 既存機能の維持 (Priority: P1)

ユーザーとして、従来通りトピックを入力してマンガ画像を生成したい。
内部アーキテクチャの変更は、ユーザー体験に影響を与えてはならない。

**Acceptance Scenarios**:

1. **Given** メインページにいる状態、**When** トピックを入力して生成ボタンをクリック、**Then** 従来通り進捗表示を経てマンガ画像が表示される
2. **Given** 生成処理中の状態、**When** 進捗状況を確認、**Then** リサーチ中→シナリオ作成中→画像生成中の順で表示される
3. **Given** エージェント処理でエラーが発生、**When** エラー状態を確認、**Then** 適切なエラーメッセージが表示される

---

### User Story 2 - 開発者のローカル開発体験 (Priority: P2)

開発者として、ローカル環境でも AgentCore Runtime を起動してテストしたい。
AWS への接続なしで開発イテレーションを回せること。

**Acceptance Scenarios**:

1. **Given** ローカル開発環境、**When** `agentcore launch -l` を実行、**Then** ローカルで AgentCore Runtime が起動する
2. **Given** ローカル AgentCore が起動している状態、**When** Web アプリから生成リクエスト、**Then** ローカルエージェントで処理される
3. **Given** ローカル環境、**When** Docker が起動している、**Then** AgentCore コンテナが正常にビルド・起動する

---

## Requirements

### Functional Requirements

- **FR-001**: Web アプリは AgentCore Runtime に HTTP でエージェント実行をリクエストできること
- **FR-002**: AgentCore Runtime は SSE/ストリーミングで進捗イベントを返却できること
- **FR-003**: AgentCore Runtime は S3 からキャラクター画像を取得できること
- **FR-004**: Web アプリはキャラクター作成時に画像を S3 にアップロードすること
- **FR-005**: 生成完了時、AgentCore は生成画像（base64）と生成タイトルを返却すること
- **FR-006**: エラー発生時、AgentCore は適切なエラーメッセージを返却すること
- **FR-007**: ローカル開発時は `agentcore launch -l` でエミュレータを起動できること

### Non-Functional Requirements

- **NFR-001**: AgentCore 分離後も、既存の生成処理時間を維持すること（HTTP オーバーヘッドは許容）
- **NFR-002**: AgentCore Runtime は ap-northeast-1 リージョンで動作すること
- **NFR-003**: Web アプリと AgentCore 間の通信は HTTPS で暗号化されること（本番環境）

## 主要エンティティ

- **AgentCore Runtime**: AWS Bedrock AgentCore 上で動作するエージェント実行環境
- **InvokeRequest**: Web → AgentCore へのリクエスト（topic, character_name）
- **ProgressEvent**: AgentCore → Web への進捗イベント（status, progress）
- **InvokeResult**: AgentCore → Web への完了レスポンス（image, title）

## Assumptions

- AWS アカウントを保有しており、Bedrock AgentCore が利用可能
- ap-northeast-1 リージョンで AgentCore Runtime が GA 済み
- Google Gemini API は引き続き使用（AgentCore はモデルプロバイダに依存しない）
- キャラクター画像は S3 に保存し、AgentCore から参照する
- ローカル開発には Docker が必要
