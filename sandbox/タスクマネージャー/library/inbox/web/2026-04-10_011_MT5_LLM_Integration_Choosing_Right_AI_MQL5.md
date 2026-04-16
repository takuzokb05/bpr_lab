# MT5 LLM Integration: Choosing the Right AI for Your Trading System

- URL: https://www.mql5.com/en/blogs/post/767425
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-04-10

## 要約
MQL5 フォーラムの技術ブログ記事（2026年2月15日）。MetaTrader 5 に LLM を統合する際のモデル選択と接続アーキテクチャを解説。LLM を MT5 内で直接実行は不可（VRAM・シングルスレッド制約）なため、Ollama ローカルサーバー or クラウド API（OpenAI・Claude・DeepSeek）経由の Webhook 接続が推奨。DeepSeek はコストパフォーマンス最高（GPT-4o 比で数分の一）で繰り返しロジック API コールに最適。LLM の最適ユースケースは HFT・スキャルピング（サブ秒 × 不可）ではなく、高タイムフレームの方向性フィルター（1〜3秒 API 遅延が影響しない場面）。既存 EA の静的ルールを動的 LLM 判断に置き換える具体的な実装パターンを提示。
