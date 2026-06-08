# Claude Code Workflows: Deterministic Multi-Agent Orchestration

- URL: https://alexop.dev/posts/claude-code-workflows-deterministic-orchestration/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-08

## 要約
alexop.devがClaude Code Workflowsによる決定論的マルチエージェントオーケストレーションを解説。claude-code-workflowsライブラリを使い、専門エージェント（アーキテクト・実装者・レビュアー・テスター）をYAMLワークフロー定義でつなぐパターンを紹介。動的ワークフローとの違い：Workflowsは固定スクリプトで実行順序・エージェント数が確定的、Dynamic Workflowsは実行時にLLMがオーケストレーションスクリプトを生成する。本番コードベースへの適用例（TypeScript移行・大規模リファクタリング）を具体的コードで説明。GitHub: shinpr/claude-code-workflows参照。
