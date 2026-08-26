# MetaTrader 5にAIが到来：トレードが変わる！

- URL: https://www.mql5.com/en/blogs/post/774316
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-08-26

## 投稿内容
AI Has Arrived in MetaTrader 5: Trading Is Changing! (MQL5 Blog, August 19, 2026)

Analysis of MetaTrader 5's new built-in AI Assistant, covering the impact on trading workflows and the MT5 ecosystem.

Key capabilities of the built-in AI Assistant:
1. Real-time recognition of chart data, account balance, and positions
2. Natural language order placement and chart operations
3. Visual recognition of indicators on charts
4. Multi-step agentic execution (breaks complex tasks into action sequences)

The article explores how this represents a fundamental shift in MT5's architecture — no longer requiring external API integration (e.g., WebRequest to Claude/GPT) for AI-powered trading. The MT5-native AI Assistant operates within the platform itself, which has security, latency, and cost implications compared to external LLM integration.

The article also discusses: the MQL5 Lite free model that powers the assistant, the difference between the built-in assistant vs. external LLM integration via Python/WebRequest, and what this means for traders building algorithmic systems.

## 要約
MQL5ブログ（2026年8月19日）がMT5内蔵AIアシスタントについて詳報。①リアルタイムのチャート・残高・ポジション認識、②自然言語でのオーダー発注・チャート操作、③インジケーター視覚認識、④マルチステップエージェント実行が可能。MCP対応で端末内完結型の設計が特徴。従来の「WebRequest経由でClaude/GPT API呼び出し」設計との比較で、レイテンシ・コスト・セキュリティの観点で新しい選択肢となる。外部API統合なしでAIトレードが完結する点は設計の前提を変えうる。プロプライエタリなコードなしで、テキスト指示だけでアルゴリズム的タスクを実行可能。FX自動売買の開発者にとって、内蔵AI vs. 外部LLM統合の設計判断を再考する必要が生じている。
