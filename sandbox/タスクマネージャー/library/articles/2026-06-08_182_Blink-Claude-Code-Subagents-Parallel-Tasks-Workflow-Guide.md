# Claude Code Sub-Agents: Run Multiple Tasks in Parallel (2026 Guide)

- URL: https://blink.new/blog/claude-code-subagents-parallel
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-08

## 要約
Blink.newによるClaude Codeサブエージェント並列実行の実践ガイド。サブエージェントは独立コンテキストウィンドウで動作し、メインセッションを汚染せずに複数タスクを同時実行できる。.claude/agents/ディレクトリへのYAML定義でエージェント仕様（モデル・ツール・ロール）を設定。典型的ユースケース：コードベース並列探索、テスト実行、マルチファイルリファクタリング。Dynamic WorkflowsとAgent Teamsとの違いも解説。エージェント結果はサマリーとしてメインコンテキストに返却されるため、コンテキスト消費を抑制できる。
