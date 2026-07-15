# エンジニアが入れるべきMCPサーバー厳選まとめ 2026（Zenn）: Filesystem・Draw.io・Serena他

- URL: https://zenn.dev/imohuke/articles/mcp-servers-2026
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-06-24

## 要約
ZennのimohukによるMCPサーバー品質基準付き厳選まとめ。選定基準：①実務継続使用できる安定性（テスト済み）、②セキュリティリスクの低さ（信頼できるソース）、③Claude Code / Claude Desktop両対応。14,000+サーバーが乱立する中、本当に使える定番サーバーに絞った価値ある資料。推薦サーバー：Filesystem（ローカルファイル操作・公式）、GitHub MCP（公式・PR/Issue/コード操作）、Draw.io（図表生成）、Serena（コードベース理解・LSP統合）、AWS MCP（公式・AWSサービス操作）、MDN（公式・Web標準）。設定例（claude mcp add コマンド・claude_desktop_config.json両方）付き。特筆：Serenaはコードベース全体の依存関係・コールグラフを理解するLSP統合型サーバーとして、大規模プロジェクトでの活用価値が高いと評価。
