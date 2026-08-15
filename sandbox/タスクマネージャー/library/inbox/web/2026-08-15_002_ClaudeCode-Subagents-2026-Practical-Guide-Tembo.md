# Claude Code Subagents: A 2026 Practical Guide

- URL: https://www.tembo.io/blog/claude-code-subagents
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-15

## 要約
Tembo.io によるClaude Code サブエージェント実践ガイド。サブエージェントをどう起動するか（fork vs 新規）、並列実行のパターン（worktree 分離 vs 共有）、200件上限撤廃後の設計思想、コスト管理の考え方を解説。特に subagent_type: "fork" によって親セッションの会話コンテキストとプロンプトキャッシュを引き継ぐことでコスト削減できる点を具体例付きで説明。エラーリトライ・タイムアウト処理の実装例も含む。
