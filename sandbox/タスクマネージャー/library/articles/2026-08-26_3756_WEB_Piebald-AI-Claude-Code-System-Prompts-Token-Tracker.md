# GitHub: Piebald-AI/claude-code-system-prompts — 全システムプロンプト＆トークン数トラッカー

- URL: https://github.com/Piebald-AI/claude-code-system-prompts
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-26

## 投稿内容
Repository: Piebald-AI/claude-code-system-prompts

All parts of Claude Code's system prompt, 27 builtin tool descriptions, sub agent prompts (Plan/Explore/Task), utility prompts (CLAUDE.md, compact, statusline, magic docs, WebFetch, Bash cmd, security review, agent creation). Updated for each Claude Code version.

As of Claude Code v2.1.246 (August 25th, 2026), the repository contains an up-to-date list of all Claude Code's various system prompts and their associated token counts.

In June 2026, the repository greatly expanded from 350 to 515 prompts (+165), representing their most complete coverage.

Key tracked components:
- Agent Prompt: Explore (862 tokens)
- Agent Prompt: Plan mode enhanced (1,066 tokens)
- 27 builtin tool descriptions
- Sub-agent prompts (Plan/Explore/Task)
- Utility prompts: CLAUDE.md, compact, statusline, magic docs, WebFetch, Bash cmd, security review, agent creation

Note: Some prompts contain interpolated bits (builtin tool name references, available sub-agents lists, context-specific variables), so actual counts in a Claude Code session differ slightly (±20 tokens).

## 要約
Claude Codeの全システムプロンプトとトークン数をバージョンごとに追跡するOSSリポジトリ。v2.1.246（2026年8月25日）時点で515件以上のプロンプトを収録。含まれる内容：①メインシステムプロンプト、②27個の内蔵ツール定義、③サブエージェントプロンプト（Plan/Explore/Task）、④ユーティリティプロンプト群（CLAUDE.md・compact・statusline・magic docs・WebFetch・Bashコマンド・セキュリティレビュー・エージェント作成）。Agent Prompt: Explore=862トークン、Plan mode=1,066トークンなど具体的なトークン数を記録。内部変数（ツール名リスト・利用可能サブエージェント等）を含むものは±20程度の誤差あり。Claude Codeの内部動作の研究・コスト最適化・プロンプト設計改善に活用できる一次情報ソース。Claude Code開発者・研究者向けの必須参照リポジトリ。
