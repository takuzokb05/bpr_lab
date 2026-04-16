# Claude Code サブエージェント活用ガイド — 公式ブログ

- URL: https://claude.com/blog/subagents-in-claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-15

## 投稿内容
Anthropic's official guide on when and how to use subagents in Claude Code. Subagents are specialized agents invoked from the main agent, each with their own context window, tools, and persona. Best for parallelizable, file-independent tasks: bulk refactoring, migrations, test generation. Not for tightly sequential workflows. Subagents cannot invoke the Skill tool — only main agent context can. Token costs scale with number of agents. Current limitation: subagents & skills integration requires workarounds (GitHub issue #38719). Known patterns: planner, code-reviewer, security-reviewer specializations.

## 要約
Anthropic公式ブログによるClaude Codeサブエージェント活用ガイド。サブエージェントは独自のコンテキストウィンドウ・ツール・ペルソナを持つ専門エージェント。**並列化可能なタスク（大規模リファクタ・マイグレーション・テスト生成）に最適**で、密結合な順次ワークフローには不向き。現行の重要制約：サブエージェントからSkillツールは呼び出せず、メインエージェントのみ使用可能（issue #38719で改善議論中）。エージェント数に比例してトークンコストが増加する点も注意。planner/code-reviewer/security-reviewerの役割分担パターンが推奨。公式一次情報として実装判断の基準になる内容。
