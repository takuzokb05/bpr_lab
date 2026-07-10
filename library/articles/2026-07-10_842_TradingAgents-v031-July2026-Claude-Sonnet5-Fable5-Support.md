# TradingAgents v0.3.1：Claude Sonnet 5/Fable 5対応・安定性修正（2026年7月）

- URL: https://github.com/tauricresearch/tradingagents/releases
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-07-10

## 投稿内容

TauricResearchが2026年7月5日にTradingAgents v0.3.1をリリース。前バージョンv0.3.0（6月22日）に続く正確性・安定性修正パッチ。

**v0.3.1（2026年7月5日）主要変更内容**

追加機能：
- Claude Sonnet 5 および Fable 5 モデルのサポートを追加
- AWS Bedrock APIキー認証サポート
- `llm_max_retries`による設定可能なLLMリトライ予算

バグ修正：
- Alpha VantageファンダメンタルズペイロードがJSON文字列のため、dict-onlyガードがフィルタリングをサイレントにスキップしていた問題を修正
- ニュースアナリストツールのドキュメント不一致を修正
- 共有debate/riskルーターが実行中にクラッシュする問題を修正
- チェックポイント再開時にグラフ形状設定が尊重されない問題を修正
- StockTwitsとRedditのcrypto sentiment解決を改善

**v0.3.0（2026年6月22日）主要変更内容**

- 全ベンダーパスにわたるシンボル正規化を含む検証済みデータアクセスコントラクト
- NVIDIA NIM・Kimi（Moonshot）・Groq・Mistral・Amazon Bedrock（ネイティブ）等の新プロバイダーをサポート
- FREDマクロ指標とPolymarketイベント確率の新データベンダー追加
- Claude・OpenAI・Googleモデルでの設定可能な推論深度
- GitHub Actions CI（Python 3.10〜3.13）
- ヘッドレス実行向け`TradingAgentsGraph.save_reports()`メソッド追加

TradingAgentsはLLM駆動の専門家ロール（ファンダメンタルズアナリスト・センチメントアナリスト・ニュースアナリスト・テクニカルアナリスト・多様なリスクプロファイルのトレーダー）でプロ取引会社の分業構造を模倣したオープンソースフレームワーク。研究目的のフレームワークであり投資アドバイスではない。

## 要約
TradingAgents v0.3.1（2026年7月5日）はClaude Sonnet 5・Fable 5の最新モデルに対応した安定性修正パッチ。AWS Bedrock APIキー認証と設定可能なLLMリトライ予算も追加。Alpha Vantageフィルタリングバグ・ルーターのクラッシュ・チェックポイント再開問題など実運用上の重要バグを複数修正。v0.3.0（6月22日）では検証済みデータアクセスコントラクト・NVIDIA/Kimi/Groq/Bedrock等のプロバイダー拡張・FREDとPolymarketの新データソース追加が行われた。GitHubスター数は執筆時点で80K超（急成長中）。Claude Sonnet 5をトレーディングエージェントの推論エンジンとして活用できるようになった点が実践的に重要。
