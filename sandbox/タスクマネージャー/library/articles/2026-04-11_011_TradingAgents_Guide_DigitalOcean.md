# TradingAgents Multi-Agent LLM Framework Guide（DigitalOcean）

- URL: https://www.digitalocean.com/resources/articles/tradingagents-llm-framework
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-04-11

## 要約
DigitalOceanが公開したTradingAgents LLMフレームワーク実践ガイド。GPU Droplet上でのセットアップから金融シミュレーション実行まで解説。アーキテクチャ詳細：7役割のエージェント（Fundamentals Analyst・Sentiment Analyst・News Analyst・Technical Analyst・Researcher・Trader・Risk Manager）がLangGraphのDAGで協調。Bull/Bear研究者が市場条件を議論し、Risk Managerが最終ポジションサイズを承認するフロー。対応LLMプロバイダー：OpenAI・Google・Anthropic・xAI・OpenRouter・Ollama。2026年2月リリースのv0.2.0でGPT-5.x・Gemini 3.x・Claude 4.x・Grok 4.xのマルチプロバイダー対応が追加。FX自動取引システムへの応用（マルチエージェント化）の参考として有用。
