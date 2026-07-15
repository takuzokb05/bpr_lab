# MetaTrader MCP Server: AI LLM Trading Automation

- URL: https://agentpedia.codes/mcp/metatrader-mcp
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-19

## 要約
Agentpedia による MetaTrader MCP サーバーの解説ページ。MetaTrader 4/5 と LLM（Claude・GPT 等）を MCP プロトコル経由で接続する仕組みを解説。従来の EA（Expert Advisor）が固定ロジックのみだったのに対し、MCP 経由で LLM をリアルタイム推論エンジンとして組み込むことで動的な意思決定が可能になる。具体的なツール定義（open_trade・close_trade・get_ohlc・get_account_info 等）と JSON-RPC レスポンス形式を示す。MQL5 の HTTP 制限を Python ブリッジで迂回する実装パターンを紹介。MT5 の OnTick() 内に LLM 呼び出しを直接埋め込む設計の欠陥（スループット不足・タイムアウトリスク）も明示。本番環境に向けたキューベースのアーキテクチャ（MT5 → Python キュー → LLM → 実行）を推奨。
