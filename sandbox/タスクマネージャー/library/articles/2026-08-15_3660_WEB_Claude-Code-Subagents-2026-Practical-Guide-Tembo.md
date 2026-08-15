# Claude Code Subagents: A 2026 Practical Guide

- URL: https://www.tembo.io/blog/claude-code-subagents
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-15

## 要約
Tembo.io によるClaude Code サブエージェント実践ガイド。fork vs 新規サブエージェントの使い分け（fork型：親会話コンテキスト・プロンプトキャッシュ継承でコスト削減、新規型：独立コンテキストが必要な場合）、worktree 分離 vs 共有の選択基準、200件上限撤廃後の設計思想（フラット型→階層型エージェント組織）、コスト管理（キャッシュヒット率最大化・エフォートレベル調整）を解説。エラーリトライ・タイムアウト処理の実装例、並列実行でのレース条件回避パターンも含む。本番運用経験に基づいた実践的な内容。
