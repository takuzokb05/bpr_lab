# Building an AI Trading Bot with Claude Code: A 961 Tool Call Case Study

- URL: https://explore.n1n.ai/blog/building-ai-trading-bot-claude-code-case-study-2026-03-16
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-04-07

## 要約
Claude Codeを使って暗号通貨トレーディングボットをゼロから構築した14セッション・961ツール呼び出しの詳細ケーススタディ（2026年3月16日公開）。1つのCLAUDE.mdプロンプトから27ファイルが生成。15戦略をバックテストして生き残った戦略は1つのみ（EMA Momentum、最も少ないトレード数の戦略）。セッション12では5エージェントを同時起動して各エージェントが戦略を設計し、結果ミーティングで絞り込み。90日・26,000本の5分足ローソク足で検証。重要知見：①CLAUDE.mdの質がコード品質を直接規定する、②docs/STATUS.mdへの継続的状態書き込みでセッション断絶からの高速復帰、③「本番mainnetでは確認後に取引」ルールをClaudeが自律的に遵守（安全性確認）。Claude Code × FXトレーディングの橋渡し事例として最高の一次情報。
