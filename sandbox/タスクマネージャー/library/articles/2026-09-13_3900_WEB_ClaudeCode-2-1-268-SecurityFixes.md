# Claude Code 2.1.268: Deny-Rule Bypass Fix, MCP Secret Leak Fix

- URL: https://freedom.tech/posts/2026-09-10-claude-code-2-1-268/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-13

## 要約
Claude Code 2.1.268（2026-09-10）の重要セキュリティ修正2件: (1) `!`で始まるdenyルールが設定ソース外にスコープリークしていた問題を修正——複数の設定レイヤー（project/user）を持つ環境で重要 (2) シンボリックリンク経由のディレクトリにEdit/Write/Read denyルールが実パス使用時に適用されなかった問題を修正。加えてセキュリティ影響あり: `/mcp`および`claude mcp list`が`${VAR}`プレースホルダーから解決したシークレットをターミナル出力に表示しなくなった。その他改善: WebFetchが300秒タイムアウト（CLAUDE_CODE_WEBFETCH_DEADLINE_MS環境変数で変更可）・アイドル時CPU固定の修正。denyルールを使っているチームは2.1.268へのアップデートを強く推奨。
