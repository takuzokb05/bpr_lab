# MetaTrader MCPサーバー: 32ツールで自然言語からMT5を操作するオープンソースブリッジ

- URL: https://github.com/ariadng/metatrader-mcp-server
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-05-30

## 投稿内容
metatrader-mcp-server — GitHub, ariadng. Open-source MCP server that bridges AI assistants (Claude Desktop, ChatGPT via Open WebUI, etc.) to MetaTrader 5 via Model Context Protocol. 32 trading tools: real-time price and historical data retrieval, account balance/margin monitoring, market/limit order placement/modification/closing, position management. Three interface options: MCP server, REST API, WebSocket stream. Tech requirements: Python 3.10+, MT5 terminal with algorithmic trading enabled, login/password/server credentials (stored locally only, not transmitted). WebSocket Quote Server enables real-time tick data streaming. Use case: "Buy EUR/USD at 0.01 lots" spoken in natural language, AI agent executes via MT5. Significant disclaimer: trading involves substantial risk; developer bears no liability.

## 要約
GitHubで公開されているオープンソースMCPサーバー「metatrader-mcp-server」がMCP経由でAIアシスタントとMT5を接続する実用ブリッジ。Claude Desktop等から「EUR/USDを0.01ロット買う」などの自然言語指示でMT5を操作可能。提供する32ツール：リアルタイム価格・過去データ取得、口座残高・証拠金確認、市場/指値注文の発注・変更・決済、ポジション管理等。インターフェースはMCPサーバー・REST API・WebSocketストリームの3種。技術要件：Python 3.10以上、MT5アルゴ取引有効化、認証情報（ローカルマシン上のみ保持）。WebSocket Quote Serverでティックデータのリアルタイムストリーミングも可能。MCPエコシステムとFXアルゴ取引を直結するエントリーポイントとして、本リポジトリの「FX自動取引」サンドボックスとの親和性が高い実践ツール。
