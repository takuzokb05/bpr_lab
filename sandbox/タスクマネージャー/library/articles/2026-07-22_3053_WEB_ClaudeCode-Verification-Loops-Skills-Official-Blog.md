# Building verification loops in Claude Code with skills — Anthropic Blog

- URL: https://claude.com/blog/building-verification-loops-in-claude-code-with-skills
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-22

## 投稿内容
Official Anthropic blog post (July 22, 2026) on automating verification loops using Claude Code skills. The core concept: most agentic coding sessions follow a loop of gather-context → act → verify → loop. By encoding recurring manual checks as skills (markdown files in .claude/skills/), Claude can close these feedback loops autonomously. Four deployment patterns: Standalone (manually invoked: security scans, accessibility audits), Embedded (built into other skills to auto-run), Chained (one skill triggers another sequentially), PR-wide (enforced on every pull request team-wide). Skills can encode business logic generic linters can't catch: e.g. "Reject any migration that drops a column without a backfill step." Toolchain integrations include linters, type checkers, GitHub Actions, and custom rubrics for grading outcomes. Efficiency compounds: "The check you wrote down to save yourself two minutes a week is now saving everyone two minutes a week, on every change."

## 要約
Anthropic公式ブログ（7月22日）。Claude Codeのスキルを使ってVerification Loopを自動化する手法を解説。スキルは .claude/skills/ 配下の Markdownファイルで定義し、フロントマター（名前・説明・許可ツール）と手順を記述するだけ。4パターン（スタンドアロン・埋め込み・チェーン・PR全体）で柔軟に活用可能。汎用リンターが検出できないビジネスルール（「backfillなしのカラムdropは拒否」等）をスキルとして実装する実践例を紹介。チームで使えば1人の節約が全員の節約になる。Claude Code自律化の鍵となるパターン。
