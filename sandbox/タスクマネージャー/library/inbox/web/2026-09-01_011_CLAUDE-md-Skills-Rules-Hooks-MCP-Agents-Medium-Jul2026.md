# CLAUDE.md, Skills, Rules, Hooks, MCP, Agents

- URL: https://jorgepit-14189.medium.com/claude-md-skills-rules-hooks-mcp-agents-045f3131d78f
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-01

## 要約
George Pipis（Medium）による 2026年7月の Claude Code 全拡張機能を一気通貫で解説した記事。5層アーキテクチャの整理: (1) CLAUDE.md — エージェントの「constitution」、セッション毎に読み込む設定。(2) Skills — SKILL.md 単一ファイルで構成する再利用可能な手続き。(3) MCP Servers — 外部ツール・データ接続（GitHub/Postgres/Linear/Sentry 等）。(4) Hooks — ループの固定ポイントで自動実行される確定的コード。(5) Subagents — 独立した研究・レビュー作業のための並列エージェント。実践的な使い分け指針: 「ルールを強制したいなら Hooks、文脈知識なら Skills、委任境界なら Subagents、常時プロジェクト指針なら CLAUDE.md（短く）」。
