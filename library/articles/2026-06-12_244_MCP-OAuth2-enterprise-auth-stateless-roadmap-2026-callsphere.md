# MCP 2026エンタープライズ認証ロードマップ — OAuth 2.1・ステートレス化・ガバナンス

- URL: https://callsphere.ai/blog/model-context-protocol-mcp-2026-roadmap-scalability-enterprise-auth
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-12

## 要約
CallSphereによるMCP 2026エンタープライズ実装ロードマップ解説。現状課題: ステートフルセッションがロードバランサーと衝突・標準エンタープライズ認証なし・ガバナンスツール不在。2026-07-28 RC仕様（最終版）の核心技術: (1) ステートレスコア — 通常HTTPインフラで動作可能・ラウンドロビン負荷分散対応・Mcp-Methodヘッダールーティング・tools/list TTLキャッシュ、(2) OAuth 2.1必須化 — MCPサーバーはOAuthリソースサーバーとして公式分類、APIキー認証はエンタープライズユースケースで非推奨予定、(3) Tasks拡張 — 長時間実行ジョブサポート、(4) MCP Apps — サーバーレンダリングUI提供、(5) 正式非推奨ポリシー導入。実装推奨: 今からOAuth 2.1で設計開始・ロードバランサー対応設計を採用。背景: 97Mマンスリーダウンロード・81K GitHubスターでデファクトスタンダード確立後の成熟フェーズ移行。
