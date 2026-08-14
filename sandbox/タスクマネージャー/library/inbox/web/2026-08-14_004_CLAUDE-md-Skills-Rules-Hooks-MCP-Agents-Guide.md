# CLAUDE.md, Skills, Rules, Hooks, MCP, Agents — Complete Guide

- URL: https://jorgepit-14189.medium.com/claude-md-skills-rules-hooks-mcp-agents-045f3131d78f
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-14

## 要約
Claude Codeの全拡張機能を体系化したMedium記事（2026年7月）。CLAUDE.mdは「エージェントの憲法」として毎セッション自動ロード、Skills（.claude/skills/SKILL.md）は特定作業時のみ呼び出し、Rules（.claude/rules/）は段階的ルール管理、Hooksは全ツール呼び出しの前後に確定実行、MCPはDB/Jira/ブラウザ等の外部接続、Agentsはサブエージェント分岐。各層の使い分け基準：「常時適用」→CLAUDE.md、「特定作業時のみ」→Skills、「コードで強制」→Hooks、「外部接続」→MCPと明確に整理。Claude Code内蔵スキル一覧（/code-review, /debug, /batch, /loop等）も記載。
