# Testing LLM-Driven Trading on MetaTrader 5

- URL: https://medium.com/@thibauld1263/table-of-contents-f92f9ae840de
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-04-10

## 要約
Medium の thibauld1263 氏による LLM 駆動 MT5 取引の実験レポート（2026年1月）。Python で MT5 ブリッジを構築し、LLM（GPT-4o・Claude・DeepSeek）に価格データ・インジケーター・ニュース要約を入力して売買判断させる実装を構築。バックテスト結果として特定の LLM プロンプト設計がランダムよりも有意な成績を示したケースを報告。LLM への入力フォーマット（OHLCV + RSI + MACD 数値 + 最新ニュース見出し）、プロンプトエンジニアリングの試行錯誤、MT5 の Python API (MetaTrader5 ライブラリ) の具体的な使い方、API コストと実行速度のトレードオフを詳細に記録。実際に手を動かした実験ログとして FX 自動取引開発の参考になる。
