# MCP ステートレス化の全技術詳細: 2026-07-28リリース候補解説

- URL: https://mcpplaygroundonline.com/blog/mcp-stateless-2026-release-candidate
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-14

## 投稿内容
MCP Goes Stateless: What the 2026 Release Candidate Means for Developers — technical breakdown from MCP Playground Online.

Core changes:
- Removes initialize/initialized handshake and Mcp-Session-Id header (breaking change)
- Protocol version, client info, capabilities now travel inline in _meta field on each request
- Any server instance can serve any request → round-robin load balancing enabled
- New: Mcp-Method and Mcp-Name headers for gateway/rate-limit routing without body inspection
- New: ttlMs and cacheScope in list/resource-read responses for predictable caching
- Extensions framework: reverse-DNS IDs, ext-* repos, version independently of spec
- Deprecations (12-month minimum window): Roots, Sampling, Logging
- Final spec: July 28, 2026; 10-week SDK validation window active now

## 要約
MCP Playground Onlineによる2026-07-28 Release Candidate技術詳解。最大の変更はステートレスプロトコルコアへの移行: initialize/initializedハンドシェイクとMcp-Session-Idヘッダーを廃止し、プロトコルバージョン・クライアント情報・ケイパビリティを各リクエストの_metaフィールドに乗せるように変更（破壊的変更）。これによりラウンドロビン型ロードバランサーで分散できるようになり、スケーラビリティが大幅に向上。新規追加: Mcp-MethodとMcp-Nameヘッダー（ゲートウェイ・レートリミット用でbody inspectionなしでルーティング可能）、ttlMsとcacheScopeフィールド（キャッシュ制御）。Extensionsフレームワーク: リバースDNS IDで識別、ext-*リポジトリで独立バージョン管理。廃止予定（最低12ヶ月猶予）: Roots・Sampling・Logging。10週間のSDKバリデーション期間終了後2026年7月28日に正式リリース。Tier 1 SDKはこの期間内での対応が求められる。
