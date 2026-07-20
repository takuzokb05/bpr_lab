# MCP's 2026 Update Makes Remote Servers Easier to Scale

- URL: https://hackernoon.com/mcps-2026-update-makes-remote-servers-easier-to-scale
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-19

## 要約
HackerNoonによるMCP 2026-07-28仕様変更の技術解説。最大の変更点は「ステートレス化」: Mcp-Session-Idヘッダとプロトコルレベルのセッション管理が廃止され、任意のリクエストをどのサーバーインスタンスにもルーティング可能に。Streamable HTTPトランスポートにMcp-MethodとMcp-Nameヘッダが追加され、ロードバランサー・ゲートウェイがボディを解析せずにルーティング可能。List/リソース読み取り結果にttlMsとcacheScopeが追加（HTTP Cache-Controlモデル）。普通のHTTPインフラでMCPサーバーをスケールできるようになり、スティッキールーティングや共有セッションストアが不要に。
