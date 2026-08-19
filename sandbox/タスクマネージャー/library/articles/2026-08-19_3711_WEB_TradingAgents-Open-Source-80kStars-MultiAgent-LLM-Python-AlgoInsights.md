# TradingAgents: An Open-Source Multi-Agent LLM Trading Framework in Python

- URL: https://algoinsights.medium.com/tradingagents-an-open-source-multi-agent-llm-trading-framework-in-python-48a8e4bdd1be
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-08-19

## 投稿内容
AlgoInsightsによるTradingAgents（TauricResearch）の詳細解説（Medium）。

## 要約
TradingAgentsの詳細: GitHub 80,000+スター・15,500+フォーク（最大手オープンソースAIトレードFW）。技術仕様: LangGraph上に構築、7エージェント構成（4アナリスト→2リサーチャー（買い論/売り論）→リスクマネージャー→トレーダー）。4アナリストは並列実行で構造化レポートを生成。リサーチャーは同データで対立する論陣を構築、リスクマネージャーが両論を評価してポジションサイジングルール適用後トレーダーに指示。LLMバックエンド: GPT/Claude/Gemini/Grok対応。実績: AAPL 26.62%累積リターン vs buy-and-hold -5.23%（2024年6-11月バックテスト）。
