# Claude Code Setup Definitive Guide: CLAUDE.md, MCP Servers, Skills, Hooks（LLMx）

- URL: https://llmx.tech/blog/definitive-guide-to-claude-code-setup-claude-md-mcps-skills/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-11

## 要約
LLMx Blogによる4拡張システム（CLAUDE.md・MCPサーバー・スキル・フック）の体系的ガイド。重要知見：MCPサーバーのツールはフックのtoolイベントでmcp__<server>__<tool>形式で呼び出し可能。Hooksの12種のうち実務で最も使われるのはPreToolUse（tool実行前）とPostToolUse（tool実行後）。April 2026アップデートで追加されたProcessStart/ProcessEndフックの活用法も紹介。CLAUDE.mdは「Progressive Disclosure」の原則に従い、情報の場所を教えるだけにとどめ詳細はスキルに委ねる設計が推奨される。最大コンテキスト消費量を抑えながら専門知識を必要時に展開するアーキテクチャ設計の参考になる。
