# MCP 2026-07-28 仕様正式リリース — Bringing Stateless MCP to Claude（Anthropic公式）

- URL: https://claude.com/blog/bringing-mcp-2026-07-28-to-claude
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-28

## 投稿内容
The final MCP 2026-07-28 specification shipped today, July 28, 2026. Key changes: stateless protocol core (request/response model), eliminates initialize handshake and Mcp-Session-Id header. Extensions framework (SEP-2133) with reverse-DNS IDs and independent versioning. MCP Apps (sandboxed HTML UI) and stateless Tasks promoted to first-class official Extensions. Enterprise managed authorization extension (stable) + beta SDKs in Python, TypeScript, Go, C#. Breaking changes: tasks/list removed, Roots/Sampling/Logging deprecated, error code -32002 → -32602. Old and new implementations do not silently interoperate. Anthropic is bringing this to all Claude clients as of today.

## 要約
本日（2026-07-28）MCP最大改訂仕様が正式リリース。①ステートレスコア：プロトコル層がリクエスト/レスポンス型に移行、ラウンドロビンLBでリモートMCPサーバーが動作可能 ②initializeハンドシェイクとMcp-Session-Idヘッダーを廃止 ③Extensionsフレームワーク（SEP-2133）：MCP Apps・ステートレスTasksが公式拡張に昇格 ④Enterprise認可拡張（stable）+ Python/TS/Go/C# SDK ベータ。破壊的変更：tasks/list削除、Roots/Sampling/Logging非推奨。AnthropicはClaudeへの適用を本日発表。既存MCPサーバーの移行が必要。
