# Claude Code v2.1.172 Nested Sub-Agents Depth=5: Builder Guide

- URL: https://chatforest.com/builders-log/claude-code-nested-sub-agents-depth-5-token-math-builder-guide/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-05

## 要約
2026年6月10日にBoris ChernyがClaude Code v2.1.172でネストされたサブエージェント（depth=5）を実装。従来は「サブエージェントは子エージェントを生成不可」という制約があったが撤廃。主要詳細：①最大5階層の階層型エージェントオーケストレーション実現、②各エージェントが独立したコンテキストウィンドウを保持するためコンテキスト管理に有効、③5階層制限は意図的設計（コスト爆発とオブザーバビリティ崩壊防止）。ユースケース：マルチステップコードレビューパイプライン、専門サブエージェントによる調査ワークフロー、テストスイート別CI/CDオーケストレーション。
