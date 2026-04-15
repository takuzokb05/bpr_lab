# How and when to use subagents in Claude Code (Anthropic Official)

- URL: https://claude.com/blog/subagents-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-15

## 要約
Anthropic公式ブログによるClaude Codeサブエージェント活用ガイド。サブエージェントは独自のコンテキストウィンドウ・ツール・ペルソナを持つ専門エージェント。**並列化可能なタスク（大規模リファクタ・マイグレーション・テスト生成）に最適**で、密結合な順次ワークフローには不向き。現行の重要制約：サブエージェントからSkillツールは呼び出せず、メインエージェントのみ使用可能（issue #38719で改善議論中）。エージェント数に比例してトークンコストが増加する点も注意。planner/code-reviewer/security-reviewerの役割分担パターンが推奨。公式一次情報として実装判断の基準になる内容。
