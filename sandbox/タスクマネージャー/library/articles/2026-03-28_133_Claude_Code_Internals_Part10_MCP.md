# Claude Code Internals, Part 10: MCP Integration (Medium / Marco Kotrotsos)

- URL: https://kotrotsos.medium.com/claude-code-internals-part-10-mcp-integration-713baf4e4e68
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

Claude Code内部実装のリバースエンジニアリングシリーズ第10回。MCPのClaude Code内部実装を詳細分析：
- **トランスポート方式**: STDIO・SSE・Streamable HTTPの3方式とそれぞれの使い分け
- **ToolSearch機能**: MCPツール定義をすべてプロンプトに含めず動的ロードすることで、コンテキスト使用量を最大**46.9%削減**
- ツール定義のロード順序とメモリ上での管理構造
- MCPサーバー接続時のリトライ・タイムアウト挙動

実測データを含む技術解析で、MCPを多数登録している環境でのパフォーマンス最適化に直接役立つ内容。
