# How to Connect AI Agents to MetaTrader 5 via MCP

- URL: https://www.mql5.com/en/articles/21905
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-05-07

## 要約
MetaTrader 5（MT5）にMCP（Model Context Protocol）経由でAIエージェントを接続する方法を解説した技術記事（MQL5公式サイト掲載）。MQL5でMCPサーバーを実装してMT5の口座情報・注文・履歴データをClaudeやGPT-4等のLLMから参照・操作する手順を詳述。JSON-RPCベースのMCP通信をMQL5内でハンドリングし、Tools定義（get_balance、place_order、get_positions等）を公開する実装例を含む。FX自動取引とLLMエージェントの直接統合を実現する希少な一次情報。MT5+MCPの組み合わせはAI取引エージェント構築における重要なアーキテクチャパターン。
