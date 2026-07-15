# Claude Code決定版セットアップ: CLAUDE.md・MCPサーバー・Skills・Hooks完全手順

- URL: https://llmx.tech/blog/definitive-guide-to-claude-code-setup-claude-md-mcps-skills/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-29

## 投稿内容
How to Set Up Claude Code (2026): CLAUDE.md, MCP Servers, Skills, Hooks — the definitive setup guide covering all four pillars. CLAUDE.md serves as the "project constitution" with tech stack, coding conventions, and forbidden patterns, but becomes counterproductive beyond 200 lines as Claude starts skipping important instructions. For MCP servers, the recommended stack is Context7 (library documentation retrieval), GitHub CLI (PR operations), and Playwright (browser automation). Skills are placed in ~/.claude/skills/ as SKILL.md files — no programming knowledge required, pure Markdown. Hooks are shell commands that automatically execute on commit, tool calls, file edits, enabling safe unattended agent operation. Five-step setup: install → create CLAUDE.md → add MCP → define Skills → configure Hooks.

## 要約
Claude Codeを最大活用するためのセットアップ決定版ガイド（5ステップ構成）。CLAUDE.mdは「プロジェクトの憲法」として機能するが200行超えると重要指示を読み飛ばすため簡潔さが最重要。推奨MCPスタックはContext7（ライブラリドキュメント取得）・GitHub CLI（PR操作）・Playwright（ブラウザ自動化）の3本柱。SkillsはSKILL.mdをMarkdownで記述するだけで有効化され、プログラミング知識不要でClaude Codeに「この作業をSkillにして」と話しかけると自動生成も可能。Hooksはコミット前・ツール呼び出し後・ファイル編集時などに自動実行するシェルコマンドで無人エージェント動作を安全に実現。インストールから全設定完了まで5ステップで整理された実践的手順書として有用。
