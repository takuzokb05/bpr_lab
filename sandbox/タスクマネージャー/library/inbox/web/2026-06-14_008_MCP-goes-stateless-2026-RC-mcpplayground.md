# MCPがステートレス化へ: 2026-07-28リリース候補の何が変わるか

- URL: https://mcpplaygroundonline.com/blog/mcp-stateless-2026-release-candidate
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-14

## 要約
MCP Playground Onlineによる2026-07-28 Release Candidateの技術解説。最大の変更はステートレスプロトコルコアへの移行: initialize/initializedハンドシェイクとMcp-Session-Idヘッダーを廃止し、プロトコルバージョン・クライアント情報・ケイパビリティを各リクエストの_metaフィールドに乗せるように変更。これによりラウンドロビン型ロードバランサーで分散できるようになり、スケーラビリティが大幅に向上。新規追加: Mcp-MethodとMcp-Nameヘッダー（ゲートウェイ・レートリミット用）、ttlMsとcacheScopeフィールド（キャッシュ制御）、Extensionsフレームワーク（リバースDNS IDで識別）。廃止予定: Roots・Sampling・Logging（最低12ヶ月の廃止猶予あり）。10週間のバリデーション期間後、2026年7月28日に正式リリース予定。
