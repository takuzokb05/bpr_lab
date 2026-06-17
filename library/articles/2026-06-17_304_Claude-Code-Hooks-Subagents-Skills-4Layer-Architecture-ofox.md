# Claude Code 4層アーキテクチャ: Hooks・Subagents・Skills完全ガイド — ofox.ai

- URL: https://ofox.ai/blog/claude-code-hooks-subagents-skills-complete-guide-2026/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-17

## 要約
Claude Codeの拡張システムを「アドバイザリ層（CLAUDE.md）」「決定論層（Hooks）」「スキル層（Skills）」「並列層（Subagents）」の4層モデルで整理した設計論。核心的知見：CLAUDE.md＝知識（80%遵守）/ Hooks＝反射（100%確実）という明確な使い分け原則。実装パターン：PostToolUse hookでフォーマッタ自動実行、SKILL.md frontmatterにhooksを直書き（settings.json不要）、サブエージェントへの仕事分割基準（小・文脈内→スキル、大・並列→サブエージェント）。最小構成推奨：CLAUDE.md 1本 + MCP最小セット + 安全hook 1本 + 繰り返しskill 1本。
