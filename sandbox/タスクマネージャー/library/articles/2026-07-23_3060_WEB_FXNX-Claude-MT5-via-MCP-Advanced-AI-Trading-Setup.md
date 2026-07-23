# Claude + MT5 via MCP: Advanced AI Trading Setup Guide

- URL: https://fxnx.com/en/blog/claude-mt5-via-mcp-your-advanced-ai-trading-setup
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-07-23

## 投稿内容
ClaudeのAPI推論能力とMetaTrader 5をMCP（MetaTrader Connect Proxy）で接続するアーキテクチャガイド。3コンポーネント構成：ClaudeがMarketデータを分析し取引判断を生成、MCPがClaude⇔MT5間のセキュアな変換レイヤーとして機能、MT5が実際の注文を執行。セットアップはMT5にEAとしてMCPサーバーコンポーネントをインストールし、Pythonクライアントライブラリ経由でMCP→Claude API→MT5コマンドのパイプラインを構築。APIレイテンシの問題からH1/H4/日足での使用を推奨。ポジションサイジング上限のハードコード、デモ口座での徹底的なバックテスト、全プロンプト・レスポンスのロギングが必須安全策。ニュースセンチメント・テクニカル指標・ファンダメンタル分析の同時統合が可能な点がルールベースEAとの本質的差分。

## 要約
FXNXがClaude API + MT5 + MCP（MetaTrader Connect Proxy）の3層アーキテクチャを解説した実践ガイド。MT5にEAとして組み込むMCPサーバーがClaude APIとの通信を仲介し、Pythonスクリプトがデータ取得→LLM判断→注文実行のパイプラインを自動化。APIレイテンシ特性からH1以上のタイムフレームが適切。安全策としてポジションサイジング上限のハードコード・デモ口座バックテスト・ロギングを強調。既存のMQL5ベースEAを超えて、リアルタイムニュースセンチメント・テクニカル・ファンダメンタル分析を一括処理できるのが最大の価値。FX自動取引プロジェクトのClaude統合において直接参照できる設計パターン。
