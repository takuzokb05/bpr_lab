# Testing LLM-Driven Trading on MetaTrader 5: GPT-4o vs Claude vs DeepSeek実験報告

- URL: https://medium.com/@thibauld1263/table-of-contents-f92f9ae840de
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-29

## 要約
2026年1月発表のLLM駆動MT5取引実験報告（実装付き）。3モデル（GPT-4o・Claude 3.5 Sonnet・DeepSeek V3）をMetaTrader 5に接続しFX実トレード評価。実装方法：Pythonブリッジ（FastAPI Webhook）でMT5 EAとLLM APIを接続、5分足OHLCV＋RSI/MACD＋直近ニュースフィードをコンテキストとして提供し売買判断を取得。結果：3モデルともシャープレシオ0.3〜0.5程度、ランダムウォーク仮説を棄却できず、スプレッドコストが利益を侵食。分析：LLM単体の短期FX取引判断は困難——テクニカル指標のパターン認識は既存指標と大差なく、高頻度コンテキスト更新のコストも問題。将来展望：マルチエージェント構成（ファンダメンタルズエージェント＋テクニカルエージェント＋リスク管理エージェント）と中長期タイムフレームへの移行に可能性を見出す。実装コード付き実験レポートとして参照価値高い。
