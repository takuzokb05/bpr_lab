# Claude Code Dynamic Workflows（研究プレビュー）: 最大1,000並列サブエージェント

- URL: https://claude.com/blog/introducing-dynamic-workflows-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 要約
2026年5月28日、Claude CodeにDynamic Workflows（研究プレビュー）が追加。オーケストレーターエージェントがタスクを動的に分割し、最大1,000サブエージェントを並列実行、各自が計画・実行・検証を完結させてから統合する。同時実行上限は16（低CPUコアマシンでは少なくなる）。実例：BunプロジェクトをZigからRustに移植（75万行Rust生成、既存テストスイート99.8%通過、11日で完了）。Max/Team/Enterprise（管理者許可時）とAPI・Amazon Bedrock・Vertex AI・Microsoft Foundry向けに提供。Opus 4.8が並列サブエージェントを内部でスポーンし、コードベース規模のマイグレーションを数時間から自律的にこなす。
