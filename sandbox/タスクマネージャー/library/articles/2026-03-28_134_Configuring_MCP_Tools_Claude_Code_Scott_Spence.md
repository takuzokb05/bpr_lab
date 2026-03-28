# Configuring MCP Tools in Claude Code — The Better Way (Scott Spence)

- URL: https://scottspence.com/posts/configuring-mcp-tools-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

CLIウィザード経由ではなく `settings.json` を直接編集する方法でのMCP設定ガイド。
- **ユーザースコープ** (`~/.claude/settings.json`) vs **プロジェクトスコープ** (`.claude/settings.json`) の使い分け
- 環境変数・実行パスの渡し方を含む完全なJSONスニペット付き
- stdioサーバーとHTTPサーバーの設定差異
- 複数サーバーを登録する際の命名規則とコンフリクト回避方法

CLIウィザードでは設定できない細かい挙動制御（タイムアウト、リトライ設定）もJSONで直接指定可能。コピペですぐ使える具体例が多い。
