# Claude Code/CodexにNeo4j MCP + Hooksで永続メモリを実装するガイド

- URL: https://x.com/TDataScience/status/2052846501718544658
- ソース: x
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-08
- いいね: 1 / RT: 0
- 投稿者: @TDataScience / フォロワー 250128

## 要約
Tomaz Bratanićによるハンズオンガイドの紹介。HookとNeo4j MCPを組み合わせることで、Claude Code・Codex・Cursorに特定ツールへの依存なしで永続メモリを持たせる手法。HookがセッションをまたいだコンテキストをNeo4jグラフDBに保持し、次回セッションで参照できる設計。特定LLMツールに縛られない汎用アーキテクチャとして重要なパターン。フォロワー25万超のData Scienceアカウントが紹介。