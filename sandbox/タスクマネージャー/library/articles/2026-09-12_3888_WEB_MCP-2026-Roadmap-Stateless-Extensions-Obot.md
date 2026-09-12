# MCP is Growing Up: The 2026 Roadmap Takes Shape — Stateless Core & Extensions (Obot)

- URL: https://obot.ai/blog/mcp-is-growing-up-the-2026-roadmap-takes-shape/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-12

## 投稿内容
Analysis of the MCP 2026-07-28 Release Candidate (now final spec published July 28, 2026). Biggest change: protocol goes stateless — no handshake, no session ID, any request can hit any server instance, enabling plain round-robin load balancers without sticky routing. Protocol metadata now travels in _meta on every request; server/discover method lets clients fetch capabilities without a live connection. Extensions Framework added as first-class: MCP Apps (servers can ship sandboxed HTML UI in an iframe, templates declared upfront for security review) and Tasks (async tool calls with task handles: tasks/get, tasks/update, tasks/cancel). Auth hardening (OAuth 2.1) and formal deprecation policy. Ecosystem scale: 10,000+ public MCP servers, 97M monthly SDK downloads (as of December 2025 when Anthropic donated MCP to Linux Foundation).

## 要約
MCP 2026-07-28仕様（確定版）の分析（Obot）。最大の変更はプロトコルのステートレス化: ハンドシェイク不要・セッションID廃止・ラウンドロビンLBで運用可能・スティッキールーティング不要。_metaでプロトコルメタデータを全リクエストに付与、server/discoverで事前のケーパビリティ取得が可能。Extensionsがファーストクラスに昇格: MCP Apps（サンドボックスiframe内HTML UIをサーバーがシップ可能、セキュリティレビュー用テンプレート宣言）、Tasks（非同期ツール呼び出し、tasks/get・update・cancelで制御）。OAuth 2.1認証強化と正式廃止ポリシー追加。エコシステム規模: 公開MCP 1万台超・月間9700万SDK DL（2025-12時点、Linux Foundationへの寄贈タイミングのデータ）。
