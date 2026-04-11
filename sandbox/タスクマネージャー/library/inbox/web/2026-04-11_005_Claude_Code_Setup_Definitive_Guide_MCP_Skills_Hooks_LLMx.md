# Claude Code Setup Definitive Guide: CLAUDE.md, MCP Servers, Skills, Hooks

- URL: https://llmx.tech/blog/definitive-guide-to-claude-code-setup-claude-md-mcps-skills/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-11

## 要約
LLMx Blogが公開したClaude Code設定の決定版ガイド。4つの拡張システム（CLAUDE.md・MCPサーバー・スキル・フック）を体系的に解説。特に重要な知見：MCPサーバーのツールはフックのtoolイベントでmcp__<server>__<tool>形式で呼び出し可能。Hooksの種類12種のうち実務で最も使われるのはPreToolUse（tool実行前）とPostToolUse（tool実行後）。Claude Code April 2026アップデートで追加されたProcessStart/ProcessEndフックの活用法も紹介。CLAUDE.mdは「Progressive Disclosure」の原則に従い、情報の場所を教えるだけにとどめ詳細はスキルに委ねる設計が推奨される。英語/日本語環境どちらでも参照しやすい構成。
