# Claude + MT5 via MCP: Advanced AI Trading Setup Guide

- URL: https://fxnx.com/en/blog/claude-mt5-via-mcp-your-advanced-ai-trading-setup
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-07-23

## 要約
ClaudeのAPI推論能力とMetaTrader 5をMCP（MetaTrader Connect Proxy）で接続するアーキテクチャガイド。3コンポーネント構成：ClaudeがMarketデータを分析し取引判断を生成、MCPがClaude⇔MT5間のセキュアな変換レイヤーとして機能、MT5が実際の注文を執行。セットアップはMT5にEAとしてMCPサーバーコンポーネントをインストールし、PythonクライアントライブラリでMCP経由のマーケットデータ取得→Claude APIに構造化プロンプト送信→JSON応答をMT5コマンドにパースするスクリプトを構築。APIレイテンシの問題からH1/H4/日足などの高いタイムフレームでの使用を推奨（HFTには不適）。ポジションサイジング上限のハードコード、デモ口座での徹底的なバックテスト、全プロンプト・レスポンスのロギングが必須の安全策。ルールベースの固定システムを超え、ニュースセンチメント・テクニカル指標・ファンダメンタル分析の同時統合が可能になる点が最大の特徴。
