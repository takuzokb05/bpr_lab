# Claude Code × MCPで始めるAgent駆動開発 2026

- URL: https://netsujo.jp/blog/claude-code-mcp-agent-driven-dev-2026
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-05-08

## 投稿内容

Netsujo 株式会社のテックブログ。MCP で外部ツールと接続した Claude Code によるエージェント駆動開発の実践報告。

## 要約

「Agent駆動開発」とは MCP で外部ツールと接続した Claude Code が、人間の指示なしにタスクを自律的に実行するワークフロー。実践例3件：（1）Vercel 環境変数の末尾改行問題を Claude Code が10分で原因特定（人間なら数時間、バイト列レベルの64文字vs65文字差分を即特定）、（2）Gmail 未読メールを毎日3回 cron で取得→返信必要メールに絞って日本語下書き作成、（3）GitHub Issue 監視→自動コーディング→PR作成。MCP サーバー選定の優先順位：公式提供＞有名OSS＞自作（自作は Claude Code 自身に書かせれば1〜2時間）。セキュリティ懸念：MCP Tool Poisoning に注意（悪意あるMCPサーバーが隠しコマンドを埋め込む攻撃手法）。エラーハンドリングと監査ログの整備が本番運用の必須条件。
