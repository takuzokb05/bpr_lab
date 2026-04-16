# Claude Code Skills vs Subagents - When to Use What?

- URL: https://dev.to/nunc/claude-code-skills-vs-subagents-when-to-use-what-4d12
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-13

## 要約
Claude CodeのSkillsとSubagentsの使い分けをDEV.toで詳解した実践記事。整理の枠組み：Skills＝レシピ（ポータブルな専門知識）、Subagents＝専門職の同僚（独自コンテキストウィンドウで動く独立エージェント）。Subagents採用基準3点：①冗長な出力を本文コンテキストに入れたくない、②特定ツール制限を強制したい、③作業が自己完結してサマリーだけ返せる。複数エージェント/会話で同じ専門知識が必要な場合はSkillsを優先。起動時にSkillsをSubagentのコンテキストに注入することで「専門知識を持つSubagent」を構築可能。言語別コードレビューエージェントを例にした実装例を含む。SkillsとSubagentsの使い分け判断フローチャートが実用的。
