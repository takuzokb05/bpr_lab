# TradingAgents v0.2.4 — LangGraphチェックポイント・Docker・DeepSeek対応

- URL: https://github.com/TauricResearch/TradingAgents
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-04-27

## 要約
TauricResearchのマルチエージェントLLM金融取引フレームワーク「TradingAgents」がv0.2.4にアップデート。既存v0.2.3（本ライブラリ収録済み）からの主な追加点：①構造化出力エージェント（Research Manager・Trader・Portfolio Managerが構造化出力を使用し意思決定の一貫性向上）、②LangGraphチェックポイント再開機能（長時間実行タスクを中断→再開可能に）、③永続的意思決定ログ（agent callごとのログが自動保存）、④新プロバイダー追加（DeepSeek・Qwen・GLM・Azure OpenAI）、⑤Docker対応（コンテナでの環境分離実行）、⑥Windows UTF-8エンコーディング修正。7つの役割（ファンダメンタルズ・センチメント・ニュース・テクニカルアナリスト、リサーチャー、トレーダー、リスクマネージャー）でポートフォリオ判断を協調。DeepSeek V4 Proが7倍低コストであることを考慮するとコスト効率面でDeepSeekバックエンドが魅力的。研究目的のフレームワークであり投資助言ではない。
