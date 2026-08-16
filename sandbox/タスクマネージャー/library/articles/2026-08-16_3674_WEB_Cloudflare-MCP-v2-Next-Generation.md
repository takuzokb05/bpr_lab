# The next generation of MCP | Cloudflare Blog

- URL: https://blog.cloudflare.com/mcp-v2/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-16

## 投稿内容
Cloudflare's official blog post on MCP v2 (2026-07-28 spec) support and the architectural implications for running MCP servers on Cloudflare Workers. Explains how the stateless protocol core removes the need for sticky sessions and shared session stores, enabling round-robin load balancing. Details OAuth 2.1/OIDC authorization hardening and the Extensions framework.

## 要約
Cloudflare が MCP 2026-07-28 新仕様への対応と次世代MCPの展望を解説したブログ。新仕様ではプロトコルがステートレス化され、従来のスティッキーセッション・共有セッションストアが不要になり、ラウンドロビンロードバランサーで動作可能になった。OAuth 2.1 / OpenID Connectによる認証強化でエンタープライズ対応が本格化。Cloudflare Workers上でのMCPサーバー構築ガイドも含む。MCPの物理インフラをCloudflareのエッジで担う設計思想を公式エンジニアが解説した一次情報。MCPサーバーの本番運用を考えている場合の参考情報。
