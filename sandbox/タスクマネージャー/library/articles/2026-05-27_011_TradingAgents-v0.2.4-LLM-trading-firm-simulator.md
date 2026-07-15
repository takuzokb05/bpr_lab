# TradingAgents v0.2.4: 証券会社を模倣する12エージェントLLM取引フレームワーク（AAPL +26.62%）

- URL: https://dev.to/_46ea277e677b888e0cd13/tradingagents-v024-a-multi-agent-llm-framework-that-simulates-an-entire-trading-firm-g2e
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-05-27

## 投稿内容
DEV CommunityによるTradingAgents v0.2.4（UCLA Tauric Research、2026年4月25日リリース）の解説記事。

## 要約
LangGraphベースのマルチエージェントLLM取引フレームワーク。5層・約12エージェント構成：ファンダメンタル・センチメント・テクニカルアナリスト（複数）、リサーチャー、トレーダー（異なるリスクプロファイル）、リスクマネージャー（7役割）。7つのLLMエージェントが互いに議論しコンセンサスでトレード決定→単一モデルのバイアスを排除。LLMバックエンド：GPT・Claude・Gemini・Grokをサポート（Claudeが選択肢に含まれる）。パフォーマンス実績：AAPL（2024年6〜11月）累積リターン26.62% vs バイアンドホールドの-5.23%。GitHubスター51,300超・フォーク9,300超（2026年4月）。LLMが決算説明会・ニュース・ソーシャルセンチメントと構造化価格データを単一パイプラインで処理する革新的アーキテクチャ。sandbox/FX自動取引への応用検討対象として最重要フレームワーク。
