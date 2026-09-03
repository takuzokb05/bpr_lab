# How to Architect an AI Agent for MetaTrader 5 — MQL5公式ブログ実装ガイド

- URL: https://www.mql5.com/en/blogs/post/774492
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-09-03

## 投稿内容

MQL5公式ブログ（2026年8月21日）によるMetaTrader 5向けAIエージェントのアーキテクチャ設計ガイド。3つの統合パターンと実装上の注意点を解説。

## 要約

MT5向けAIエージェントを「LLM-in-the-Loop」「LLM-as-Orchestrator」「LLM-as-Executor」の3アーキテクチャに分類して比較（MQL5公式ブログ）。
MT5 AI Assistant組み込み機能（MCPプロトコル対応、2026年8月リリース）との統合を詳説。
実行モジュール（OrderSend/修正/クローズ）の責務分離が鍵で、ポジション照合とAPIエラーハンドリングの実装パターンを例示。
ローカルLLM（Ollama）活用でインターネット接続なしの構成も可能。
スキャルパー（スピード優先）とスウィング（調査優先）でのLLM活用の使い分けを提案。
FX自動取引プロジェクトのMT5統合に直結する一次情報。
