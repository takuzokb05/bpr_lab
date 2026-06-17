# Claude Code Sub-Agents Explained: Context, Cost, and Parallel Execution - MindStudio

- URL: https://www.mindstudio.ai/blog/claude-code-sub-agents-explained
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-17

## 要約
Claude Codeサブエージェントのコンテキスト分離・コスト・並列実行を定量的に分析。各サブエージェントは独立コンテキストウィンドウを持ち、メインセッションのトークン消費を抑制。並列実行の最適台数は3〜5（それ以上はサマリーマージコストが増大）、Dynamic Workflows導入後は数十〜数百台まで拡張可能。リサーチ型サブエージェントはファイル書き込み禁止、ライター型はProduction API呼び出し禁止などの権限分離設計パターンを解説。コスト試算例付き。
