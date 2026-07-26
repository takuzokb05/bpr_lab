# Migrate Your MCP Server to the 2026-07-28 Spec（MCP Playground Online）

- URL: https://mcpplaygroundonline.com/blog/migrate-mcp-server-2026-07-28-stateless
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-26

## 要約

MCP Playground OnlineによるMCPサーバー移行ガイド。2026-07-28仕様への対応として：initialize ハンドシェイク削除・セッションレス化・_meta フィールド追加・エラーコード変更（-32002→-32602）の4点が主な対応箇所。TypeScript・Python双方のコードサンプル付きで before/after を比較。ステートレス化でテスト容易性が上がる点を強調（各リクエストが独立するためユニットテストが書きやすい）。MCPの新しいApps・Tasks拡張を使ってステートフルな長時間実行タスクを代替する方法も解説。段階的な移行パスを提供しており既存MCPサーバー保守者に有用。
