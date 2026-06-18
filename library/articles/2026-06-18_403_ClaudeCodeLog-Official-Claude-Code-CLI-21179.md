# Official Claude Code CLI 2.1.179 changelog: fixes mid-stream connection drops 

- URL: https://x.com/ClaudeCodeLog/status/2066982484533817550
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-18
- いいね: 3 / RT: 1 / リプライ: 1
- 投稿者: @ClaudeCodeLog / フォロワー 70,258

## 投稿内容

Claude Code CLI 2.1.179 changelog:

Fixes:
• Fixed mid-stream connection drops: partial responses are now preserved instead of showing a raw error, and the spinner no longer gets stuck at "running tool"
• Fixed mouse-wheel scrolling in WSL2 under Windows Terminal and VS Code (regression in 2.1.172)
• Fixed a sandbox denyRead/allowRead glob over a large directory tree making the Bash tool description enormous and the session unusable on Linux
• Fixed the feedback survey capturing a single-digit reply as a session rating immediately after a turn completes
• Fixed the welcome screen stacking multiple promotional banners — at most one promo now shows per session
• Fixed Ctrl+O not showing the subagent's transcript when viewing a subagent
• Fixed clicking the prompt input not returning focus from the subagent/footer panel
• Fixed remote session background tasks appearing stuck as "still running" between turns

Improvement:
• Improved plugin loading performance in remote sessions

Source: https://t.co/6jtHD4BrWv

## 要約

Official Claude Code CLI 2.1.179 changelog: fixes mid-stream connection drops preserving partial responses, and WSL2 mouse-wheel scrolling regression from 2.1.172。
投稿者 @ClaudeCodeLog（フォロワー70,258人）によるclaude-code関連情報。
投稿内容の要点: Claude Code CLI 2.1.179 changelog:
