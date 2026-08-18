# TradingAgents v0.3.1 リリース: Claude Sonnet 5 / Fable 5 対応・安定性修正（2026年7月）

- URL: https://tauricresearch.github.io/TradingAgents/
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-08-18

## 要約
TauricResearch（UCLA+MIT共同研究）のTradingAgents v0.3.1が2026年7月にリリース。主な修正・機能追加:
- **Claude Sonnet 5 / Fable 5 サポート追加**: 最新AnthropicモデルへのネイティブサポートでFX/株取引エージェントの精度向上が期待される
- **Alpha Vantage ルックアヘッドフィルタリング修正**: バックテストでの未来データ使用バグを修正（重大な正確性修正）
- **グラフルーターのクラッシュ安全性向上**: 複数エージェント間の通信ルーターの安定性改善
- **グラフ形状対応チェックポイント再開**: 長時間実行の中断・再開が可能に
- **暗号資産センチメントソース修正**: 動作しなくなっていたデータソースを修正
- **設定可能なLLMリトライバジェット**: レート制限時の挙動を制御可能に
- **Bedrock API-keyAuth**: AWS Bedrock経由でのClaude利用が容易に
FX自動取引プロジェクトでTradingAgentsを活用する場合、v0.3.1へのアップデートでClaude Sonnet 5のパフォーマンスを最大限活用できる。ただしバックテストのシャープレシオ5-8は統計的異常であることを著者も明記しており、実資金での運用には慎重な検証が必要。
