# Manganize Constitution

<!--
Sync Impact Report:
Version: 1.0.0 (Initial Constitution)
Ratification Date: 2025-11-29
Changes:
  - Initial constitution creation for Manganize project
  - Established 6 core principles: Spec駆動開発, 型安全性, EARS記法準拠, Divioドキュメンテーション, コード品質, LangGraphベース設計
  - Defined governance model with amendment procedures and compliance review
  - Specified technical stack constraints and technology selection principles

Template Consistency:
  ✅ plan-template.md - Updated Constitution Check section with concrete compliance checklist based on 6 principles
  ✅ spec-template.md - Added EARS syntax guidance to Requirements section
  ✅ tasks-template.md - Added code quality verification tasks (ruff, mypy, type hints) to Polish phase
  ✅ agent-file-template.md - Reviewed, no updates needed (constitution-agnostic template)
  ✅ checklist-template.md - Reviewed, no updates needed (constitution-agnostic template)

Documentation Updates:
  ✅ AGENTS.md - Added explicit reference to Constitution at the top
  ✅ README.md - Added Constitution reference in contribution section

Follow-up Actions:
  - None - Initial constitution fully defined and all dependent artifacts updated
  - Future: As docs/specs/ features are created, ensure they follow the Spec-Driven Development principle
-->

## Core Principles

### I. Spec駆動開発（Spec-Driven Development）

**原則**: 仕様と実装は常に同期していなければならない（MUST）。

- すべての機能は `docs/specs/` 配下に対応する仕様ファイルを持つこと
- 各機能ディレクトリは `requirements.md`、`design.md`、`tasks.md` を含むこと
- コードを変更したら、対応する Spec ファイルの更新を検討すること
- 1つの巨大な Spec ファイルではなく、機能ごとに分離すること

**根拠**:
仕様と実装の乖離は、技術的負債の最大の原因となる。Spec駆動開発により、意図と実装の一致を保証し、開発者間のコミュニケーションコストを削減する。また、探索的な実装後に仕様を固める逆フローも許容することで、柔軟性と厳密性のバランスを取る。

### II. 型安全性（Type Safety - NON-NEGOTIABLE）

**原則**: すべての関数に型ヒントを付与しなければならない（MUST）。

- すべての関数シグネチャに引数と戻り値の型ヒントを付与すること
- `mypy` でエラーが出ないことを確認してからコミットすること
- 型ヒントのない関数は実装として不完全とみなす

**根拠**:
Python は動的型付け言語だが、型ヒントにより静的解析が可能になり、バグの早期発見とIDEサポートの向上が実現される。LangGraph/LangChainとの統合では、状態管理の型安全性が特に重要である。この原則は交渉不可能（NON-NEGOTIABLE）であり、例外は認められない。

### III. EARS記法準拠（EARS Compliance）

**原則**: requirements.md では EARS（Easy Approach to Requirements Syntax）記法を使用しなければならない（MUST）。

EARS パターン:
- **Ubiquitous**: 「システムは〜すること」（常に成り立つ要件）
- **Event-driven**: 「〜の場合、システムは〜すること」（イベント駆動の要件）
- **State-driven**: 「〜の状態のとき、システムは〜すること」（状態依存の要件）
- **Optional**: 「ユーザーが〜を選択した場合、システムは〜すること」（オプション機能）

曖昧な表現（「〜すべき」「〜かもしれない」など）は避け、明確な動詞と条件を使用すること。

**根拠**:
EARS記法は、要件の曖昧性を排除し、テスト可能な要件定義を可能にする。特に、LLMベースのシステムでは、非決定的な動作が発生しやすいため、要件の明確化が品質保証の鍵となる。

### IV. Divioドキュメンテーション（Divio Documentation System）

**原則**: ドキュメントは Divio システムの4象限に従って整理しなければならない（MUST）。

`docs/wiki/` 配下の構造:
- **tutorials/**: チュートリアル（学習指向）- 初めての方向けの手順書
- **how-to/**: ハウツーガイド（問題解決指向）- 特定の課題を解決する方法
- **reference/**: リファレンス（情報指向）- 技術仕様とAPIドキュメント
- **explanation/**: 解説（理解指向）- システムの背景と設計思想

各ドキュメントは適切な象限に配置し、目的を明確にすること。

**根拠**:
Divio システムは、ドキュメントの目的を明確化し、ユーザーが必要な情報に素早くアクセスできるようにする。学習、問題解決、参照、理解という4つの異なるニーズに対応することで、ドキュメントの有用性が大幅に向上する。

### V. コード品質（Code Quality）

**原則**: コードは `ruff` と `mypy` による品質チェックに合格しなければならない（MUST）。

- `ruff check .` でリント警告がないこと
- `ruff format .` でフォーマットが統一されていること
- `mypy manganize/` で型チェックエラーがないこと
- コミット前に必ずこれらのチェックを実行すること

**根拠**:
自動化された品質チェックは、コードレビューの負担を軽減し、スタイルの一貫性を保証する。特に、AI エージェントとの協調開発では、コーディング規約の自動化が重要である。

### VI. LangGraphベース設計（LangGraph-Based Architecture）

**原則**: エージェント実装は LangGraph の状態管理パターンに従わなければならない（MUST）。

- `AgentState` で状態を型安全に管理すること
- チェックポイント機能を活用して会話履歴を保存すること
- ツールは `tools.py` に分離し、独立してテスト可能にすること
- プロンプトは `prompts.py` に分離し、バージョン管理すること

**根拠**:
LangGraph は複雑なエージェントフローを管理するための強力なフレームワークであり、状態管理の明確性と拡張性を提供する。パターンに従うことで、チーム全体が一貫したアーキテクチャを維持し、将来的な機能追加が容易になる。

## 開発ワークフロー

### 基本フロー（Spec → 実装）

1. **要件定義**: `requirements.md` で要件を定義または更新
2. **設計更新**: `design.md` で実装方針を設計
3. **タスク生成**: `tasks.md` でタスクを生成または更新
4. **実装**: タスクに沿ってコードを実装
5. **品質チェック**: `ruff` と `mypy` でコード品質を確認
6. **Spec更新**: 実装により仕様に変更があれば Spec を更新

### 逆フロー（実装 → Spec）

探索的な実装や試行錯誤の後に仕様を固める場合も許容される：

1. 実装を行う（プロトタイピング）
2. 「この変更を Spec に反映して」と依頼
3. 適切な Spec ファイルを更新
4. 必要に応じて `design.md` と `tasks.md` を更新

### コミット規約

Angular Convention に従うこと：

| プレフィックス | 用途 |
|---------------|------|
| `feat:` | 新機能 |
| `fix:` | バグ修正 |
| `docs:` | ドキュメントのみの変更 |
| `style:` | コードの意味に影響しない変更（フォーマット等） |
| `refactor:` | バグ修正でも機能追加でもないコード変更 |
| `perf:` | パフォーマンス改善 |
| `test:` | テストの追加・修正 |
| `chore:` | ビルドプロセスや補助ツールの変更 |

## 技術スタック制約

### 必須技術

- **言語**: Python 3.13 以上
- **パッケージ管理**: uv
- **フレームワーク**: LangGraph / LangChain
- **LLM**: Google Generative AI (Gemini)
- **開発ツール**: mypy（型チェック）、ruff（リント・フォーマット）

### 推奨される追加技術

- **タスクランナー**: Task（Taskfile.yml）
- **画像処理**: Pillow
- **環境変数管理**: python-dotenv

### 技術選定の原則

新しい依存関係を追加する場合：

1. 必要性を明確に文書化すること（`design.md` に記載）
2. 代替案との比較を行うこと
3. ライセンスの互換性を確認すること
4. メンテナンス状況を確認すること（最終更新が6ヶ月以内を推奨）

## Governance

### 憲章の優先順位

この憲章はすべての開発プラクティスに優先する。憲章と矛盾する場合は、憲章の原則に従うこと。

### 改訂手続き

憲章の改訂には以下の手順を踏むこと：

1. **提案**: 改訂の必要性と具体的な変更内容を文書化
2. **議論**: チームでの議論と合意形成（該当する場合）
3. **文書化**: 改訂内容と根拠を Sync Impact Report に記載
4. **バージョン管理**: セマンティックバージョニングに従ってバージョンを更新
   - MAJOR: 後方互換性のない原則の削除または再定義
   - MINOR: 新しい原則の追加または既存原則の大幅な拡張
   - PATCH: 明確化、文言修正、誤字修正、非意味的な改良
5. **伝播**: 依存するテンプレートとドキュメントを更新

### コンプライアンスレビュー

すべての Pull Request とコードレビューは、この憲章への準拠を確認すること：

- [ ] Spec ファイルが更新されているか（必要な場合）
- [ ] 型ヒントが付与されているか
- [ ] `ruff` と `mypy` のチェックに合格しているか
- [ ] ドキュメントが適切な象限に配置されているか
- [ ] コミットメッセージが規約に従っているか

### エージェント向けガイダンス

AI コーディングエージェントは `AGENTS.md` を参照し、この憲章に従って開発を行うこと。`AGENTS.md` は実行時のガイダンスを提供し、この憲章は根本的な原則を定義する。両者は補完的な関係にある。

### 複雑性の正当化

原則に違反する場合（例: 型ヒントの省略、EARS記法からの逸脱）は、その理由を明確に文書化し、代替案が拒否された理由を説明すること。正当化なしの違反は許容されない。

**Version**: 1.0.0 | **Ratified**: 2025-11-29 | **Last Amended**: 2025-11-29
