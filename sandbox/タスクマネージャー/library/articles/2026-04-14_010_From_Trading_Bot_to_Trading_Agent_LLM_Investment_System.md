# From Trading Bot to Trading Agent: How to Build an AI-based Investment System

- URL: https://medium.com/@gwrx2005/from-trading-bot-to-trading-agent-how-to-build-an-ai-based-investment-system-313d4c370c60
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-04-14

## 投稿内容
Architecture evolution from rule-based trading bots to LLM-driven trading agents. Covers agent design with multi-source data integration, TradingAgents framework integration, and honest discussion of LLM trading limitations.

## 要約
ルールベースのトレーディングボット→LLM駆動エージェントへのアーキテクチャ進化を解説する実践記事（Medium）。**ボットとエージェントの本質的違い**：ボット=固定ルール実行機、エージェント=目標達成のための自律的意思決定システム。エージェント設計の核心：LLMが市場データ・ニュース・テクニカル指標を統合的に解釈し「なぜ今買うか/売るか」を推論する。**実装コンポーネント**：①市場データパイプライン②ニュース/センチメント分析③LLMによるトレード決定エンジン④リスク管理レイヤー⑤実行エンジン。TradingAgentsフレームワーク（ファンダメンタル・センチメント・テクニカルの3エージェント並列）との統合例を掲載。**LLMトレードの限界**（突発的マクロイベント・ブラックスワンへの対応困難）を正直に説明している点が誠実で実用的。AI自動取引システムを設計したい開発者向けの実践的ロードマップ。
