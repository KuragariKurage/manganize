# Tutorials（チュートリアル）

**学習指向** - Manganize を初めて使う方向けの手順書です。

チュートリアルは、実際に手を動かしながら学ぶことを目的としています。順番に実行することで、Manganize の基本的な使い方とコンセプトを理解できます。

## 📚 利用可能なチュートリアル

### 1. はじめての Manganize

[はじめての Manganize →](getting-started.md)

**対象読者**: Manganize を初めて使う方

**所要時間**: 約 15 分

**学べること**:
- プロジェクトのセットアップ
- API キーの設定
- 最初の漫画の生成
- 自分のテキストを漫画化する方法

**前提条件**:
- Python 3.13 以上
- uv がインストールされていること
- Google Generative AI の API キー

---

### 2. LangGraph を理解する

[LangGraph を理解する →](understanding-langgraph.md)

**対象読者**: LangGraph の基本を学びたい方

**所要時間**: 約 20 分

**学べること**:
- LangGraph の基本概念
- エージェントの状態管理
- ツールの仕組み
- チェックポイント機能
- 独自のツールを追加する方法

**前提条件**:
- [はじめての Manganize](getting-started.md) を完了していること
- LangChain の基本的な知識

---

## 推奨される学習順序

```
1. はじめての Manganize
   ↓ 基本的な使い方を学ぶ

2. LangGraph を理解する
   ↓ 内部の仕組みを理解する

3. How-to Guides に進む
   ↓ 実践的なカスタマイズ方法を学ぶ

4. Explanation を読む
   ↓ 設計思想を深く理解する
```

## 次のステップ

チュートリアルを完了したら、以下のドキュメントに進むことをお勧めします。

### How-to Guides（問題解決指向）

- [プロンプトをカスタマイズする](../how-to/customize-prompt.md)
- [カスタムツールを追加する](../how-to/add-custom-tool.md)
- [画像品質を最適化する](../how-to/optimize-image-quality.md)

### Reference（リファレンス）

- [API リファレンス](../reference/api.md)
- [設定リファレンス](../reference/configuration.md)

### Explanation（解説）

- [アーキテクチャ解説](../explanation/architecture.md)
- [設計の意思決定](../explanation/design-decisions.md)
- [プロンプトエンジニアリング解説](../explanation/prompt-engineering.md)

## フィードバック

チュートリアルに関するフィードバックや質問は、GitHub の Issue でお願いします。

- わかりにくい箇所
- 追加してほしいトピック
- 誤字・脱字

## 関連リソース

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Generative AI Documentation](https://ai.google.dev/gemini-api/docs)

