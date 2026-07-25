# Build a Multi-Agent AI Trading System with TradingAgents 2026

- URL: https://blog.pickmytrade.io/build-a-multi-agent-ai-trading-system-with-trading-agents-2026/
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-07-25

## 投稿内容

PickMyTradeによるTradingAgentsフレームワークを使ったマルチエージェントAI取引システムの構築チュートリアル（2026年版）。

## 要約

- TradingAgents（Apache 2.0、TauricResearch）を使ったマルチエージェント取引システムの実装チュートリアル
- 7エージェント構成: 4つのアナリストエージェント（並列実行・構造化レポート生成）→ Bull/Bear Researcher（対立論拠の構築）→ Risk Manager（エビデンス評価・ポジションサイジング）→ Trader（最終実行）
- LLMバックエンドとしてGPT・Claude・Gemini・Grokを選択可能。7月時点のv0.3.1ではClaude Sonnet 5をサポート
- 決算報告書・ニュース・SNSデータ・価格データを並列アナリストが処理し、上位エージェントに集約する設計
- リスク管理の組み込み方: Risk Managerエージェントへのシステムプロンプト設計とポジションサイジングロジック
- バックテスト環境の構築と、本番移行前の検証プロセスについても解説
- MT5や証券APIとの統合パターンについて言及あり（直接統合より中間APIレイヤーを推奨）
