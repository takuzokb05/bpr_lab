# The MCP 2026-07-28 Rewrite: What Breaks and How to Migrate

- URL: https://www.developersdigest.tech/blog/mcp-2026-07-28-breaking-changes
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-08

## 要約
Developers DigestによるMCP 2026-07-28仕様の破壊的変更と移行ガイド。主要変更：①handshake廃止（initialize/initializedハンドシェイクとMcp-Session-Idヘッダーを完全削除）②ステートレスプロトコルへの移行（ラウンドロビンロードバランサーで動作可能に）③HTTP+SSEトランスポートの非推奨化（1年のofframpあり）④MCPアプリ（server-rendered UI）とタスク拡張（長時間実行ワーク）の追加⑤OAuth/OIDCに準拠した認可体系。移行コストの試算と具体的なコード変更例を提供。既存のsteamedful MCPサーバーを持つ開発者向けに、いつ移行すべきか、何が壊れるかを詳解。
