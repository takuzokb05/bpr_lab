# Claude Agent SDK完全ガイド — Messages API対比・MCP3層統合・本番セーフガード

- URL: https://hidekazu-konishi.com/entry/claude_agent_sdk_complete_guide.html
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-08-01

## 投稿内容
hidekazu-konishi.comによる2026年6月版Claude Agent SDK技術解説。Messages APIとの比較表、MCP統合3層アーキテクチャ、`@tool`デコレータ・`createSdkMcpServer()`、`allowed_tools`命名規則（`mcp__<server>__<tool>`）、本番安全ガイドライン。

## 要約
Claude Agent SDKとMessages APIの本質的違いを「ループの所有者」で整理した技術記事。SDK：「Claudeがループを所有」→モデル実行・ツール実行・コンテキスト管理がSDK側。Messages API：「完全な手動制御」→カスタムワークフロー向け。実用的なMCP統合は3層構成：①built-in tools（実装不要）②インプロセスカスタムツール（`@tool`デコレータ/`createSdkMcpServer()`）③外部MCPサーバー（stdio/HTTP/SSE）。ツール命名は`mcp__<server>__<tool>`が規約。本番パターンの核心：（1）必ず`max_turns`設定（暴走ループ防止）、（2）`can_use_tool`コールバックで実行時判断、（3）無人実行は`dontAsk`（fail-closed）モード必須、（4）`allowed_tools`最小限設定、（5）`session_id`記録による再開可能ワークフロー、（6）`disallowed_tools`は`bypassPermissions`下でもブロック。著者の原則：「自律性より先に権限境界を保ち、3ツール+厳格allowlistの読み取り専用エージェントから開始」。
