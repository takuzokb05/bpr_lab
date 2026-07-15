# TradingAgents Python Tutorial: LLM Trading Firm Simulator (algoinsights Medium)

- URL: https://algoinsights.medium.com/tradingagents-an-open-source-multi-agent-llm-trading-framework-in-python-48a8e4bdd1be
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-02

## 要約
algoinsightsByMediumによるTradingAgentsフレームワークのPython実践チュートリアル。
TradingAgentsはUCLA+MITチームが開発したLangGraphベースのオープンソースフレームワーク（GitHub 51,300+ stars）。7つのLLMエージェント（ファンダメンタルアナリスト・センチメントアナリスト・ニュースアナリスト・テクニカルアナリスト・ブル/ベアリサーチャー・トレーダー・リスクマネージャー）が取引ファームをシミュレート。
TradingAgents v0.2.0（2026年2月）でGPT-5.x・Gemini 3.x・Claude 4.x・Grok 4.xのマルチプロバイダー対応追加。
チュートリアルの実装手順: `pip install tradingagents`→APIキー設定→シンボル・日付範囲指定→エージェントチーム起動→レポート生成。
注意事項: AAPL+26.62%はバックテスト値（2024年6-11月）であり、著者らがSharp比が統計的異常値であることを明示している。実取引への展開には慎重な検証が必要。
