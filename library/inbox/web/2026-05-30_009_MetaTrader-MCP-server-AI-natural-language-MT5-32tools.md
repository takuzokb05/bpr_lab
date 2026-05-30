# MetaTrader MCPサーバー: AI自然言語でMT5を操作する32ツールブリッジ

- URL: https://github.com/ariadng/metatrader-mcp-server
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-05-30

## 要約
GitHub上のオープンソースプロジェクト「metatrader-mcp-server」がMCP（Model Context Protocol）を通じてAIアシスタントとMetaTrader 5を接続する。Claude Desktop・ChatGPT（Open WebUI経由）等から自然言語でMT5を操作可能。提供する32ツール：リアルタイム価格・過去データ取得、口座残高・証拠金確認、市場注文・指値注文の発注/変更/決済、ポジション管理等。インターフェースはMCPサーバー・REST API・WebSocketストリームの3種。技術要件：Python 3.10以上、MT5ターミナルでアルゴリズム取引を有効化、認証情報（ログイン番号・パスワード・サーバー名）。認証情報はローカルマシン上にのみ保持するセキュア設計。WebSocket Quote Serverでティックデータのリアルタイムストリーミングも可能。MCPエコシステムとFXアルゴ取引を直結する実践的ブリッジで、AI駆動トレード実験のエントリーポイントとして注目度が高い。
