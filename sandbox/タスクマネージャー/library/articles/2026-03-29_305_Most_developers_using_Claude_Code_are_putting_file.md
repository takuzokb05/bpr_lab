# Most developers using Claude Code are putting files in the wrong place.

- URL: https://x.com/tut_ml/status/2037396170461606300
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-29
- いいね: 32 / RT: 5 / リプライ: 2
- 投稿者: @tut_ml / フォロワー 25,952

## 投稿内容

Most developers using Claude Code are putting files in the wrong place.

Here's the structure that actually works 👇

Skills → .claude/skills/ (not a root skills/ folder) Agents → .claude/agents/Commands → .claude/commands/

These 3 mistakes alone cost me days.

The other things nobody tells you:

→ PostToolUse matcher needs "Edit|MultiEdit|Write":  just "Write" and your linter hook silently does nothing 

→ SessionStart and SessionEnd are real hook events (half the internet says they don't exist) 

→ npm install is no longer how you install Claude Code. Native installer is. 

→ MAX_THINKING_TOKENS is the real env var for thinking budget

Made the full reference sheet so you don't have to read 8 different doc pages.

## 要約

（要約は次回 /curate 時に追記）
