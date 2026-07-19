# MCP's 2026 Update Makes Remote Servers Easier to Scale

- URL: https://hackernoon.com/mcps-2026-update-makes-remote-servers-easier-to-scale
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-19

## 要約
HackerNoonによるMCP 2026-07-28仕様変更の実践的技術解説。最大の変更点「ステートレス化」の詳細: Mcp-Session-Idヘッダとプロトコルレベルのセッション管理が廃止され、任意のMCPリクエストをどのサーバーインスタンスにもルーティング可能に（スティッキールーティング・共有セッションストアが不要）。Streamable HTTPトランスポートにMcp-MethodとMcp-Nameヘッダが追加され、ロードバランサー・ゲートウェイがボディ解析なしにルーティング可能。List/リソース結果にttlMsとcacheScopeが追加（HTTP Cache-Control準拠）。普通のHTTPインフラでMCPサーバーをスケールできるようになったことで、AWS ALB・CloudflareなどのPaaS上での展開が容易になる。既存のMCP実装に対するBreaking Changesも解説。MCP 2026-07-28仕様の実装者・利用者向けの実践解説として有用。
