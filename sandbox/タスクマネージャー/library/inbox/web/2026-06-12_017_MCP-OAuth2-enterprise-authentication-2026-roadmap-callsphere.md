# MCPエンタープライズ認証 2026ロードマップ — OAuth 2.1・ステートレス化・ガバナンス

- URL: https://callsphere.ai/blog/model-context-protocol-mcp-2026-roadmap-scalability-enterprise-auth
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-12

## 要約
CallSphereによるMCP 2026ロードマップの技術的深掘り。現状の課題: ステートフルセッションがロードバランサーと衝突・標準エンタープライズ認証なし・ガバナンスツール不在。2026年RC（2026-07-28）の核心: (1) ステートレスコア — 通常のHTTPインフラで動作可能、ラウンドロビン負荷分散対応、Mcp-Methodヘッダーでルーティング、tools/listレスポンスのTTLキャッシュ、(2) OAuth 2.1必須化 — MCPサーバーはOAuthリソースサーバーとして公式分類、APIキー認証はエンタープライズユースケースで非推奨化予定、(3) Tasks拡張 — 長時間実行ジョブのサポート、(4) MCP Apps — サーバーレンダリングUI、(5) 正式な非推奨ポリシー。実装推奨: OAuth 2.1から開始し、ロードバランサー対応設計を採用。97Mマンスリーダウンロード・81K GitHubスターを背景に、MCP成熟フェーズへ移行。
