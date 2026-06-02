# TradingAgents Python チュートリアル — オープンソースLLM取引ファームシミュレーター (GitHub 51k★)

- URL: https://algoinsights.medium.com/tradingagents-an-open-source-multi-agent-llm-trading-framework-in-python-48a8e4bdd1be
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-02

## 投稿内容
algoinsightsによるTradingAgentsフレームワークのPython実践チュートリアル（Medium、2026年5月）。

**フレームワーク概要**
- 開発: UCLA+MITチーム（2026年初頭発表）
- GitHub: 51,300+ stars、9,300+ forks
- ベース: LangGraph（本記事比較で最良のAIエージェントフレームワーク1位）

**7エージェント構成（取引ファームシミュレーション）**
1. ファンダメンタルアナリスト
2. センチメントアナリスト
3. ニュースアナリスト
4. テクニカルアナリスト
5. ブル/ベアリサーチャー（対話的議論）
6. トレーダー（最終取引決定）
7. リスクマネージャー（ポジション・リスク管理）

**v0.2.0（2026年2月）の新機能**
LLMマルチプロバイダー対応: GPT-5.x・Gemini 3.x・Claude 4.x・Grok 4.x

**実装チュートリアル**
```bash
pip install tradingagents
export ANTHROPIC_API_KEY=sk-ant-...
python -c "from tradingagents import TradingAgents; ..."
```

**公表パフォーマンス（要注意）**
AAPL: +26.62%（2024年6-11月バックテスト）vs Buy-and-hold -5.23%
⚠️ Sharpe比5-8は統計的異常値で著者らも明示。実取引未経験。

P-004・P-020（TradingAgentsアーキテクチャ採用）の実装起点として最も直接的に利用可能。

## 要約
algoinsightsByMediumのTradingAgents（UCLA+MIT）Python実践チュートリアル。LangGraphベース7エージェント構成（ファンダメンタル・センチメント・テクニカル・ブル/ベア・トレーダー・リスクマネージャー）でLLM取引ファームをシミュレート。
GitHub 51,300+ stars、v0.2.0でGPT-5.x/Gemini 3.x/Claude 4.x/Grok 4.xのマルチプロバイダー対応。
`pip install tradingagents`でセットアップ、Claudeをバックエンドに指定可能。
公表パフォーマンス（AAPL +26.62%）はバックテスト値でSharpe比が統計的異常値と著者らが明示しており、実取引への転用は慎重な検証が必要。
P-004（TradingAgentsアーキテクチャ採用）・P-020（選択的コンセンサス）の具体的実装起点として活用可能。
