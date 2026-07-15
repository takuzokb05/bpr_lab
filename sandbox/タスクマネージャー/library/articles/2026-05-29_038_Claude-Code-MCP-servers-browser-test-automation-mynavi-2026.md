# Claude Codeに目と手足を与えるMCPサーバー: ブラウザ操作〜テスト自動化（マイナビ）

- URL: https://news.mynavi.jp/techplus/article/20260525-4471904/
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-29

## 投稿内容
マイナビニュース（2026年5月25日）「Claude Codeに目と手足を与える『MCPサーバー』 - ブラウザ操作からテスト自動化まで」。MCP接続でClaude Codeに「目（情報取得）と手足（操作実行）」を付与する仕組みを解説。主要MCPサーバー: Playwright MCP（ブラウザ自動操作・スクリーンショット取得）、GitHub MCP（Issue→ブランチ→PR作成の一気通貫）、Postgres/SQLite MCP（DB直接クエリ）。設定方法: `claude mcp add`コマンドまたは`.mcp.json`（プロジェクトルート配置でチーム共有可能）。MCPサーバー総数: Anthropic公式600本以上、コミュニティ製含め5,000本超、自作も可能。安全運用: 信頼スコープを「project」に限定し認証情報の過剰共有を防ぐ。

## 要約
マイナビニュース2026年5月25日掲載のClaude Code向けMCPサーバー実践ガイド。Claude CodeのMCP接続により「目（情報取得）と手足（操作実行）」を付与する概念から具体的設定方法まで解説。代表MCPとしてPlaywright（ブラウザ操作・スクリーンショット）・GitHub（Issue→ブランチ→PR一気通貫）・Postgres/SQLite（DB直接クエリ）を紹介。設定は`claude mcp add`コマンドまたは`.mcp.json`で行いプロジェクトルート配置でチーム共有が可能。MCPエコシステムはAnthropicの公式600本以上・コミュニティ含め5,000本超に成長。安全運用のポイントとして信頼スコープを「project」に限定することを明示。日本語メディアによる一般向けMCP解説として参照価値が高い。
