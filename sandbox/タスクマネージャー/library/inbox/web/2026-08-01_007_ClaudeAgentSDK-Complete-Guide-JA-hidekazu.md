# Claude Agent SDK完全ガイド — Messages APIとの違い・MCP統合・本番パターン

- URL: https://hidekazu-konishi.com/entry/claude_agent_sdk_complete_guide.html
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-08-01

## 要約
Claude Agent SDKをMessages APIと比較した技術ガイド（hidekazu-konishi.com、June 2026）。核心の違い：SDKは「Claudeがループを所有」しモデル実行・ツール実行・コンテキスト管理をSDKが担う。Messages APIは「完全な手動制御」でカスタムワークフロー向け。MCP統合は3層：①組み込みツール（実装不要）②インプロセスカスタムツール（`@tool`デコレータ）③外部MCPサーバー（stdio/HTTP/SSE）。ツール命名規則は`mcp__<server>__<tool>`。本番パターンのCritical safeguard：必ず`max_turns`を設定、`can_use_tool`コールバックで実行時判断、無人実行では`dontAsk`（fail-closed）モード、`allowed_tools`を最小限に限定、再開可能ワークフローのために`session_id`を記録。キー原則：「3ツールと厳格なallowlistを持つ読み取り専用エージェントから始め、自律性より先に権限境界を保つ」。
