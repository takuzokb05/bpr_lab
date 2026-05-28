# Claude Code Dynamic Workflows（研究プレビュー）: 最大1,000並列サブエージェントで複雑タスクを自律完結

- URL: https://claude.com/blog/introducing-dynamic-workflows-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 投稿内容
Introducing dynamic workflows in Claude Code. For the hardest tasks, Claude makes a plan, runs hundreds of parallel subagents, and verifies its work before reporting back. Think a migration touching hundreds of files. Dynamic workflows help Claude take on the most challenging tasks end-to-end. Claude dynamically writes orchestration scripts that run tens to hundreds of parallel subagents in a single session, checking its work before anything reaches you. Maximum 16 agents in concurrent execution, maximum 1,000 total agents per execution.

## 要約
2026年5月28日、Claude CodeにDynamic Workflows（研究プレビュー）が追加。オーケストレーターエージェントがタスクを動的分割し最大1,000サブエージェントを並列実行、各自が計画・実行・検証を完結してから結果を統合する自律型ワークフロー。同時実行上限16（低CPUコアマシンでは少）、総エージェント上限1,000。実証例：JarredSumnerがBunプロジェクトをZigからRustに移植（生成Rust 75万行、既存テストスイート99.8%通過、最初のコミットからマージまで11日間）。対象：Max/Team/Enterprise（管理者許可時）プランとAPI・Bedrock・Vertex AI・Microsoft Foundry向け。Claude Codeの単一線形エージェントループでは時間がかかりすぎるコードベース規模マイグレーションに特効。
