# MCP 2026-07-28 Spec: Agent Authentication with OAuth and Token Scopes

- URL: https://workos.com/blog/mcp-2026-spec-agent-authentication
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-25

## 要約
WorkOSによるMCP 2026-07-28 Release Candidate（RC）の認証変更を詳説した記事。7月28日にファイナル公開予定の最大仕様改定。
主な変更点：
- **セッションレス化**：Mcp-Session-Idヘッダ廃止、initialize/initializedハンドシェイク削除。プロトコルレベルのセッション管理が不要に
- **全リクエストへのメタ埋め込み**：プロトコルバージョン・クライアント情報・ケイパビリティを`_meta`フィールドで毎リクエストに添付
- **OAuth/OIDCとの整合**：token scopesによるツール・リソースレベルの細粒度権限制御。OktaやAzure ADとの連携が仕様レベルで定義
- **MCP Appsの導入**：MCPサーバーのパッケージング・配布の標準化
ロードバランサー対応（スティッキーセッション不要）が実現。エンタープライズでのMCPデプロイが大幅に簡素化される。
