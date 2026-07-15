# Claude Codeに目と手足を与えるMCPサーバー: ブラウザ操作からテスト自動化まで

- URL: https://news.mynavi.jp/techplus/article/20260525-4471904/
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-29

## 要約
マイナビニュース（2026-05-25）が解説するClaude Code向けMCPサーバーの実践ガイド。Claude CodeにMCPサーバーを接続することで「目（情報取得）と手足（操作実行）」を与える仕組みを解説。代表的なMCPサーバーとして、Playwright MCPによるブラウザ自動操作・スクリーンショット取得、GitHub MCPによるIssue→ブランチ→PR作成の一気通貫、Postgres/SQLite MCPによるDB直接クエリを紹介。Claude Codeからの接続設定は`claude mcp add`コマンドまたは`.mcp.json`で行い、プロジェクトルートに置くことでチーム共有が可能。MCPサーバーはAnthropicの公式リポジトリに600本以上、コミュニティ製を含めると5,000本超が存在し、自作も可能。MCP接続時は信頼スコープを「project」に限定し認証情報の過剰共有を防ぐことが安全運用の要点。
