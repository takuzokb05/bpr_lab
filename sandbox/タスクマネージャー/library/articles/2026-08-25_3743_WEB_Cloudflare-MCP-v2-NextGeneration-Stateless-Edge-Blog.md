# Cloudflare が解説する次世代 MCP v2 — エッジ統合とステートレス設計

- URL: https://blog.cloudflare.com/mcp-v2/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-25

## 要約
Cloudflare公式ブログがMCP 2026-07-28仕様（MCP v2）を解説。Cloudflare WorkersはネイティブMCPサーバーホスティングに対応し、ステートレス設計によりエッジでのゼロコールドスタート運用が可能。主要ポイント：(1) ヘッダーベースルーティングにより従来の「sticky session」問題を解消。(2) CloudflareのWAF・Ratelimiting・R2ストレージとシームレスに連携。(3) OAuth/OIDCのサポートによりエンタープライズ認証が容易化。(4) MCPサーバーの分散デプロイに最適な環境を提供。具体的な実装パターン（Workers KV + Durable Objects）も紹介。
