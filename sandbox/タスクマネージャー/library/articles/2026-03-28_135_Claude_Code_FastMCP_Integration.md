# Claude Code + FastMCP Integration (FastMCP Official)

- URL: https://gofastmcp.com/integrations/claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

FastMCP公式のClaude Code連携ガイド。FastMCPはMCPサーバーをPythonで高速に実装するフレームワーク。
- **stdio vs HTTP**モードの設定方法とそれぞれの適用シーン（ローカル開発 vs リモートデプロイ）
- `fastmcp run`コマンドでの起動とClaude Code側の設定JSON
- デコレータベースのツール定義（`@mcp.tool()`）でMCPサーバーを数十行で実装できる例
- Claude Codeからのツール呼び出し時のエラーハンドリングパターン

FastMCPを使うことでMCPサーバーの実装コストが大幅に削減でき、カスタムツールの追加が容易になる。
