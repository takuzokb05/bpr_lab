# Claude Code 20コマンドリファレンス: /rewind, /btw, /compact, /insights

- URL: https://x.com/rozzabuilds/status/2053217477010796852
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-09
- いいね: 0 / RT: 0 / リプライ: 0
- 投稿者: @rozzabuilds / フォロワー 2,353

## 投稿内容
Here are 20 Claude Code commands worth knowing, grouped by what they actually solve.

Stopping, undoing, branching

1. Esc stops the current task. Conversation history stays intact, only the in-flight action dies.

2. Double-tap Esc or /rewind opens a menu:

Restore code and conversation

Restore conversation only

Restore code only

Summarize from here

Cancel

3. /btw lets you ask a side question without polluting the main thread.

/btw where is the test file again

It reuses the existing prompt cache, so token cost is near zero.

4. /branch forks the conversation. Run two approaches in parallel, keep the one that works.

Managing the context window

5. /compact rewrites long history  into a summary that keeps the storyline, the technical decisions, and  the errors plus fixes. Context window stops bloating.

6. /clear wipes everything for a fresh topic.

7. /export saves the conversation as Markdown:

~/projects/XXX/claude-session-YYYY-MM-DD-HH-MM.md

Useful when you've spent an hour designing an architecture and don't want it to vanish.

8. /resume searches old sessions by keyword.

9. claude -c picks up yesterday's chat where you left it.

10. claude -r lists every past session and lets you jump back into a specific one.

11. /remote-control (alias /rc) hands the running session over to your phone. The work keeps executing on your machine, you just steer from somewhere else.

Working smarter

12. /model opusplan runs Opus for planning and Sonnet for execution. Slower thinking on the design, faster output on the code.

13. /simplify spins up three reviewers in parallel:

Architecture and code reuse

Code quality

Efficiency

You get one combined report.

14. /insights generates a local HTML report at ~/.claude/usage-data/report.html. It shows usage habits, common mistakes, features you've never touched, and concrete suggestions for your CLAUDE.md.

15. /loop schedules recurring or one-shot tasks inside the session:

/loop 15m check the deploy
/loop in 20m remind me to push this branch
Recurring loops auto-expire after 3 to 7 days so a forgotten schedule doesn't burn through your API budget.

You can override the default behavior by dropping a .claude/loop.md in your project. A bare /loop will then run whatever instructions you put inside.

Keyboard shortcuts

16. Ctrl+V pastes screenshots directly. No saving to disk first.

17. Ctrl+J (or Option+Enter on Mac) inserts a newline without sending. Multi-line prompts without accidents.

18. Ctrl+R searches your prompt history. Your own personal prompt library, already indexed.

19. Ctrl+U clears the entire input line in one keystroke.

20. /skills [name] loads project-specific skills. Run /skills with no argument to see what's available in the current workspace.

Credit to Deep_Structure2023 on Reddit. Great list worth sharing.

## 要約
Claude Code 20コマンドリファレンス: /rewind, /btw, /compact, /insights。投稿者@rozzabuilds（フォロワー2,353）による具体的な技術情報。
