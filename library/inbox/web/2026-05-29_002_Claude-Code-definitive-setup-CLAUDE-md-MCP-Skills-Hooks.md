# Claude Code決定版セットアップ: CLAUDE.md・MCPサーバー・Skills・Hooks完全ガイド

- URL: https://llmx.tech/blog/definitive-guide-to-claude-code-setup-claude-md-mcps-skills/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-29

## 要約
Claude Codeを最大活用するためのセットアップ完全ガイド。CLAUDE.mdは「プロジェクトの憲法」として機能し、技術スタック・コーディング規約・禁止事項を記述するが、200行超えるとClaudeが重要指示を読み飛ばすため簡潔さが重要。MCPサーバー設定ではContext7（ライブラリドキュメント取得）・GitHub CLI（PR操作）・Playwright（ブラウザ自動化）の組み合わせが推奨される。Skillsは`~/.claude/skills/`配下にSKILL.mdを置くだけで有効化され、プログラミング知識不要のMarkdown記述が基本。Hooksはコミット前・ツール呼び出し後・ファイル編集時などに自動実行するシェルコマンドで、無人エージェント動作を安全に実現する。セットアップ5ステップ（インストール→CLAUDE.md作成→MCP追加→Skills定義→Hooks設定）の具体的手順を解説。
