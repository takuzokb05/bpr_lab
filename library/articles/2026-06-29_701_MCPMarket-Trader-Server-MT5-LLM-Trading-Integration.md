# Trader MCP Server: Claude/GPTでMetaTrader 5を操作するLLM × FX統合ツール

- URL: https://mcpmarket.com/server/trader-2
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-29

## 要約
MCPMarket掲載のTrader MCP Serverは、MetaTrader 5（MT5）をModel Context Protocol経由でAI LLM（Claude・GPT等）から直接操作可能にするMCPサーバー製品。提供機能：リアルタイム価格データ取得（ティック・OHLCV）、注文執行（成行・指値・逆指値・OCO）、ポジション管理（変更・決済）、アカウント情報参照（残高・マージン・損益）、EA（Expert Advisor）制御。実装：MQL5 EA側でWebhookサーバーを立ち上げ、MCP Serverがブリッジ役となりLLMからのJSON-RPC命令を変換。Claude Code + MCP + MT5の組み合わせでFX取引エージェント構築が現実的に。LLMによるテクニカル分析→即時注文執行の自動化フローを実現するユースケースが実践的。bpr_lab FX自動取引開発への直接適用可能性あり。
