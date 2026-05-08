# TradingAgents Deployment and Practice: Building Your AI Quantitative Trading Team

- URL: https://openclawapi.org/en/blog/2026-03-21-trading-agents-deploy
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-05-08

## 投稿内容

TradingAgents フレームワークの実際の展開・実装ガイド。セットアップから MT5 統合まで。

## 要約

TradingAgents（TauricResearch 製）の実装・展開ガイド。フレームワークは LangGraph ベースで、7つの専門エージェント（Fundamental/Sentiment/News/Technical Analyst、Researcher、Trader、Risk Manager）が協調動作。対応 LLM プロバイダー：OpenAI、Google、Anthropic（Claude）、xAI、DeepSeek、Qwen（Alibaba）、GLM（Zhipu）、OpenRouter、Ollama（ローカル）、Azure OpenAI。展開手順：Python 3.10+ 環境 → API キー設定（OPENAI_API_KEY 等） → エージェント設定ファイル定義 → バックテスト実行 → VPS デプロイ。MT5 統合の要点：TradingAgents の売買シグナルを Python の MetaTrader5 ライブラリ経由でMT5に送信し自動注文執行。Claude Sonnet 4.6 は算法取引で 487% Sharpe 1.94 を達成という報告あり。研究目的フレームワークのため実運用は自己責任。
