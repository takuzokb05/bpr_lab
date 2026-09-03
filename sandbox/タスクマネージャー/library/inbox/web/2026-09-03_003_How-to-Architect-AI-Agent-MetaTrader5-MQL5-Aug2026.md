# How to Architect an AI Agent for MetaTrader 5 — MQL5 Blog Aug 2026

- URL: https://www.mql5.com/en/blogs/post/774492
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-09-03

## 要約

MQL5公式ブログ（2026年8月21日付）による、MetaTrader 5向けAIエージェントのアーキテクチャ設計実践ガイド。
LLMバックエンドとMT5の接続パターンを「LLM-in-the-Loop」「LLM-as-Orchestrator」「LLM-as-Executor」の3アーキテクチャに分類して比較。
MT5 AI Assistant組み込み機能（MCPプロトコル対応、2026年8月リリース）との統合方法を具体的に解説。
実行モジュール（OrderSend/修正/クローズ）の責務分離、ポジション照合、APIレスポンスのエラーハンドリングについて実装例付きで説明。
インターネット接続なしでのローカルLLM（Ollama）活用パターンも紹介。スピード重視のScalper型とリサーチ重視のSwing型での使い分けを提案。
