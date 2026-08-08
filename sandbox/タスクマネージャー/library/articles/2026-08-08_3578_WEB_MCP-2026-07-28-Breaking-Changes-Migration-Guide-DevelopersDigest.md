# The MCP 2026-07-28 Rewrite: What Breaks and How to Migrate

- URL: https://www.developersdigest.tech/blog/mcp-2026-07-28-breaking-changes
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-08

## 投稿内容
Breaking changes in MCP 2026-07-28: ①handshake removed (initialize/initialized + Mcp-Session-Id gone) ②stateless protocol (plain round-robin load balancers work now) ③HTTP+SSE transport deprecated (1-year offramp) ④MCP Apps (server-rendered UI) and Tasks extension (long-running work) added ⑤OAuth/OIDC-aligned authorization. Migration cost estimates and concrete code change examples for developers with existing stateful MCP servers.

## 要約
Developers DigestによるMCP 2026-07-28仕様の破壊的変更＋移行ガイド。主要変更：handshake廃止・ステートレス化（ラウンドロビンLBで動作可能）・HTTP+SSE非推奨（1年offramp）・MCPアプリ+タスク拡張追加・OAuth/OIDC準拠認可。移行コスト試算と具体的コード変更例付き。既存ステートフルMCPサーバー保有開発者向けの実践的移行ガイド。
