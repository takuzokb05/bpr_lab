# CLAUDE.md, Skills, Subagents, Hooks: When to Use Which

- URL: https://www.buildthisnow.com/blog/tools/claude-code-skills-vs-subagents-vs-hooks
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-17

## 要約
Claude Code 4プリミティブの使い分けガイド。CLAUDE.md は「常に知っておくべき知識」（リポジトリレイアウト・命名規則・ハード制約）、毎ターンロードされるため肥大化は禁物。Skills は「オンデマンドのプレイブック」、初期オーバーヘッドは約100トークン（名前と説明のみ）で必要時のみ展開。Hooks は「モデルが制御できない強制ルール」、ライフサイクルイベントで確定的に発火してモデルの判断を覆せない。Subagents は「隔離コンテキストの並列・制限付きワーカー」、約2万トークンのオーバーヘッドがあるため真にコンテキスト分離が必要な場合のみ使用。優先順序: Hooks は法律（強制）、CLAUDE.md/Skills は指針（勧告）、Subagents はスコープワーカー。
