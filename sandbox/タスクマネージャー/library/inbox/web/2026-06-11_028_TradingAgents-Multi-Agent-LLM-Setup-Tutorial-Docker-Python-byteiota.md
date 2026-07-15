# TradingAgentsセットアップチュートリアル：DockerとPythonで動かすマルチエージェントLLM取引

- URL: https://byteiota.com/tradingagents-tutorial-multi-agent-llm-trading-setup/
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-11

## 要約
TradingAgentsのセットアップから実運用までの詳細チュートリアル。7つの専門エージェント（基本アナリスト・センチメント分析・テクニカル分析・強気/弱気研究者・トレーダー・リスク管理）がLangGraphベースのグラフ上で協働。Docker（`docker compose run --rm tradingagents`）またはPython環境でデプロイ可能。9種類のLLMプロバイダ対応（OpenAI・Claude・Gemini・DeepSeek・Qwen・Azure OpenAI等）。アーキテクチャ：ノード（エージェント）とエッジ（判定ロジック）で構成、複数視点による議論でバイアス軽減。バックテスト実績：AAPL/GOOGL/AMZNで年間24.9%リターン、シャープレシオ5.60。v0.2.4（2026年4月）では永続的な意思決定ログによりエージェントが過去取引から学習可能。実運用での乖離リスク（取引コスト・スリッページ）についても警告あり。
