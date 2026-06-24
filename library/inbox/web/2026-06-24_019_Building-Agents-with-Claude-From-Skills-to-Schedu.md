# Building Agents with Claude: From Skills to Scheduled Tasks and Routines - Hatchworks

- URL: https://hatchworks.com/blog/claude/building-agents-with-claude/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-24

## 要約
HatchworksによるClaude Agentsビルディングガイド。Skills（スラッシュコマンド形式の再利用可能プロンプト）→Subagents（Agentツール経由の並列並行実行）→Routines（スケジュール・イベント駆動の自動化）という構築の段階を体系的に解説。重要な実装ポイント：サブエージェントはbypassPermissionsオプションで権限プロンプトをスキップ、worktree isolationで独立ファイル作業環境を提供、StructuredOutputスキーマで型安全な結果受け取りが可能。Claude Code Agent SDKとの使い分け（CLI vs プログラマティック）についても詳述。
