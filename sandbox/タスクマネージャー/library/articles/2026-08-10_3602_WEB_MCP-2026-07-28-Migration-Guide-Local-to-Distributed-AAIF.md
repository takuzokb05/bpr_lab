# MCP 2026-07-28: From Local Tool to Distributed Protocol - Migration Guide (AAIF)

- URL: https://aaif.io/blog/mcp-2026-07-28-whats-changing-and-how-to-migrate
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-10

## 要約
AAIF（Agentic AI Foundation）による2026-07-28 MCP仕様への移行ガイド。主要変更点「ステートレスプロトコルコア」の実装移行方法を詳説。旧来のセッション維持型サーバーからステートレス型への書き直し手順、後方互換性の確保方法、OAuth/OIDCの認証強化対応を解説。スティッキーセッションや共有セッションストアを必要としない新アーキテクチャにより、Cloudflare WorkersやVercel等の標準インフラで動作可能になる。Extensions（Apps・Tasks）フレームワークへの移行方法も含む実践的な技術ガイド。既存MCPサーバーを2026-07-28仕様に移行する際の実装参考として有用。
