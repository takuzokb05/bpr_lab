# MCP 2026-07-28 Spec: Stateless Core、正式リリース — Bringing MCP to Claude

- URL: https://claude.com/blog/bringing-mcp-2026-07-28-to-claude
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-28

## 要約
本日（2026-07-28）Model Context Protocol（MCP）の最大改訂仕様が正式リリース。RC段階（7/26収集済み）から本日最終版に。主要変更点：①ステートレスコア — プロトコル層がリクエスト/レスポンス型に移行、ラウンドロビンLBでリモートMCPサーバーが動作可能に ②initializeハンドシェイクとMcp-Session-Idヘッダーを廃止 ③Extensionsフレームワーク（SEP-2133）導入：リバースDNS形式のIDで識別、独立バージョン管理 ④MCP Apps（サンドボックスHTML UI）とステートレスTasksが公式Extensionに昇格 ⑤Enterprise向け認可拡張（stable）とPython/TypeScript/Go/C# SDK ベータ同時公開。tasks/listは削除、Roots/Sampling/Loggingは非推奨、エラーコード-32002→-32602に変更。AnthropicはClaude（すべてのクライアント）への適用を本日発表。既存MCPサーバーは移行が必要で非互換。
