# MCP 2026-07-28仕様RC: ステートレス化・Tasks拡張・OAuth強化・廃止ポリシー確立

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-30

## 投稿内容
The 2026-07-28 MCP Specification Release Candidate — Model Context Protocol Blog, May 21, 2026. The largest revision since launch. (1) Stateless protocol core: protocol-level session removed; any server instance can handle any request; sticky sessions and shared session stores no longer needed; plain round-robin load balancers work; clients can cache tools/list responses with server-defined ttlMs. (2) Extensions framework: Tasks promoted from experimental to Extension; MCP Apps adds server-rendered UI capability. (3) Authorization hardening: better alignment with OAuth 2.0 and OpenID Connect deployment practices. (4) Deprecations: Roots, Sampling, Logging deprecated with 12+ month migration window. (5) Formal deprecation policy established for protocol evolution without breaking existing builds. RC locked May 21, 2026; final spec publishes July 28, 2026 after 10-week SDK validation window.

## 要約
MCPの次期仕様リリース候補が2026年5月21日に確定し、最終版は2026年7月28日公開予定。ローンチ以来最大の改訂で5つの主要変更：(1)ステートレスプロトコル化（セッション削除・通常HTTPロードバランサー対応・tools/listキャッシュ可能化）、(2)Tasks拡張の正式化とMCP Apps（サーバーレンダリングUI）追加、(3)OAuth 2.0/OpenID Connectとの整合強化、(4)Roots・Sampling・Loggingを12ヶ月以上の移行期間付きで非推奨化、(5)正式廃止ポリシーの確立でプロトコル進化の予測可能性向上。RC確定から最終版まで10週間のSDK検証期間を設置。97M月間SDKダウンロード・5000本超サーバーエコシステム全体に影響する仕様変更。MCP対応サービス開発者は移行計画が必要。
