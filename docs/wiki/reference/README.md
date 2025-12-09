# Reference（リファレンス）

**情報指向** - 技術仕様と API ドキュメント。

## 利用可能なリファレンス

### [API リファレンス](api.md)

- `ManganizeAgent` クラス
- 状態スキーマ（Input / Output / State）
- ツール（`generate_manga_image`, `retrieve_webpage`, `read_document_file`）
- プロンプト

### [設定リファレンス](configuration.md)

- `pyproject.toml`
- `langgraph.json`
- 環境変数
- `Taskfile.yml`

## クイックリファレンス

### 基本的な使い方

```python
from manganize.agents import ManganizeAgent
from langchain.chat_models import init_chat_model

agent = ManganizeAgent()
graph = agent.compile_graph()

config = {"configurable": {"thread_id": "1"}}
result = graph.invoke({"topic": "テーマ"}, config)
```

### 環境変数

| 変数 | 説明 | 必須 |
|------|------|------|
| `GOOGLE_API_KEY` | Google Generative AI API キー | ✓ |

## 関連ドキュメント

- [Tutorials](../tutorials/) - 基本的な使い方
- [How-to Guides](../how-to/) - 実践的なカスタマイズ
- [Explanation](../explanation/) - 設計思想
