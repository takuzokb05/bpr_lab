# The 2026-07-28 MCP Specification Release Candidate（公式ブログ）

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-26

## 要約

MCP公式ブログによる2026-07-28 Release Candidate発表。最大の変更点はプロトコルをステートレス化し、セッションハンドシェイク（initialize + Mcp-Session-Id）を全廃。各リクエストに _meta フィールドでプロトコルバージョン・クライアント情報を付与する設計に移行。これによりリモートMCPサーバーが普通のロードバランサー配下で動作可能になる。Rootsサンプリング・ロギングは12ヶ月の移行期間付きで非推奨化。MCP Tasksはコアから拡張機能へ移動。公式Tier 1 SDK（Python・TypeScript等）は検証ウィンドウ内でサポートを出荷予定。月間9700万DLのエコシステムへの影響が注目される。
