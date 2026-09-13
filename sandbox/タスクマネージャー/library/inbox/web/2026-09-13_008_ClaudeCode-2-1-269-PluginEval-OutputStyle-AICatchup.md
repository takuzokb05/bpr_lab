# Claude Code 2.1.269: plugin eval, /output-style, Bash diff

- URL: https://aicatchup.com/news/claude-code-weekly-limits-permanent-25-percent-september-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-13

## 要約
Claude Code 2.1.269 (September 11, 2026) added three notable features: (1) claude plugin eval command to run a plugin's eval suite against Claude Code and get scored, reproducible results in JSON + HTML report format; (2) /output-style [name] slash command to list and switch output styles mid-session; (3) Bash tool now includes a diff of file changes in its result when it handles file edits. However, 2.1.269 introduced a regression: read-only git commands in Bash unexpectedly ask for permission after a session has been running a while. A fix is expected in 2.1.270.
