# The 2026-07-28 MCP Specification Release Candidate（MCP公式ブログ）

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-26

## 投稿内容

MCP公式ブログによる2026-07-28 Release Candidate発表。プロトコルのステートレス化、拡張機能体制への移行、セキュリティ強化（OAuth 2.0/OIDC対応）の3本柱で構成される最大規模のMCP改訂。

## 要約

- 最大の変更点はプロトコルのステートレス化：initialize ハンドシェイクと Mcp-Session-Id ヘッダーを全廃し、各リクエストの _meta フィールドにプロトコルバージョン・クライアント情報を付与する設計に移行
- これにより リモートMCPサーバーが普通のラウンドロビン型ロードバランサーで動作可能になり、エンタープライズ導入の障壁が大幅に低下
- Rootsサンプリング・ロギングは非推奨化（12ヶ月の移行期間保証付き）
- MCP Tasks機能はコアプロトコルから拡張機能（Extension）に移動。MCP Apps・MCP Tasksの2拡張がコアと並行して公式サポート
- セキュリティ: 6つのセキュリティ提案によりOAuth 2.0とOpenID Connectに準拠し、企業セキュリティレビューを大幅に簡略化
- エラーコード「リソース未見つかり」が -32002 から標準の -32602 に変更
- Anthropic Tier 1 SDK（Python・TypeScript等）は検証ウィンドウ内でサポートを出荷予定
- 月間9700万DL・1万以上のパブリックMCPサーバーという規模のエコシステムに対する最大規模の改訂
