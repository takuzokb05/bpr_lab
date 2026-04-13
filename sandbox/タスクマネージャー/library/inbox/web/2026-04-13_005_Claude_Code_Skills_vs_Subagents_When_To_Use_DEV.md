# Claude Code Skills vs Subagents - When to Use What?

- URL: https://dev.to/nunc/claude-code-skills-vs-subagents-when-to-use-what-4d12
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-13

## 要約
Claude CodeのSkillsとSubagentsの使い分けを実践的に解説したDEV.to記事。Skills＝レシピ（ポータブルな専門知識）、Subagents＝専門職の同僚（独自コンテキストで動く独立エージェント）という整理が核心。Subagents採用基準：冗長な出力を本文コンテキストに入れたくない場合、特定ツール制限を強制したい場合、作業が自己完結してサマリーだけ返せる場合。複数エージェント/会話で同じ専門知識が必要な場合はSkillsを優先。起動時にSkillsをSubagentのコンテキストに注入することで「専門知識を持つSubagent」を構築可能。SkillsとSubagentsを組み合わせた言語別コードレビューエージェントの実装例を含む実践的内容。
