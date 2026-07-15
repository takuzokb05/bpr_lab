# TradingAgents: オープンソース マルチエージェントLLM金融取引フレームワーク完全解説

- URL: https://apidog.com/blog/tradingagents-multi-agent-llm-trading/
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-25

## 要約
TauricResearch（UCLA/MIT研究者）が開発するTradingAgentsフレームワークの包括的解説記事。GitHub Stars 29,900以上、Apache 2.0ライセンス。
アーキテクチャの特徴：
- **7専門エージェント**：Fundamental Analyst・Sentiment Analyst・News Analyst・Technical Analyst・Bull Researcher・Bear Researcher・Risk Managerが協調
- **ディベート型意思決定**：Bull/Bear Researcherが対立する立場で分析し合意形成
- **マルチLLM対応**：OpenAI・Google・Anthropic・xAI・DeepSeek等主要プロバイダを統一カタログで利用可能
- **v0.2.4**（2026年4月）：構造化出力エージェント・バックテスト精度向上
実績：AAPLで2024年6〜11月バックテストにて累積+26.62%（Buy-and-hold -5.23%比）。本番運用よりリサーチ用途が推奨。claude-sonnet-4-6では487%リターン・Sharpe比1.94の報告も。
