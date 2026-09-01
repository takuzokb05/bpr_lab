# MQL5 + LLM in 2026: The Real Architecture That Works

- URL: https://www.mql5.com/en/blogs/post/769403
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-09-01

## 要約
MQL5 フォーラム（2026年4月）の実践的アーキテクチャ記事。MQL5 の制限（シングルスレッド・ブロッキング HTTP・URL ホワイトリスト制限）と LLM（確率的・高レイテンシ）の間をミドルウェアで橋渡しする構成を解説。推奨パターン: MT5 → ローカル Ollama（DeepSeek）または外部 API（OpenAI）← Webhook 中継。DeepSeek は GPT-4o 並みのロジック能力を持ちつつ 1 回あたり数分の 1 セント程度と低コスト。完全なローカル LLM 実行は VRAM 要件と MQL5 の制限から非現実的。ミドルウェア設計のチェックリスト（タイムアウト処理・フォールバック・ログ・バックテスト互換性）も提示。
