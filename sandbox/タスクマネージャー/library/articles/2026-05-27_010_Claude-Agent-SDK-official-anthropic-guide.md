# Claude Agent SDK公式ガイド: Managed Agents・セルフホストサンドボックス・Agent Teams

- URL: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-27

## 投稿内容
Anthropic公式エンジニアリングブログによるClaude Agent SDKの解説記事。

## 要約
旧称「Claude Code SDK」→「Claude Agent SDK」にリネーム（コード生成を超えた汎用エージェント構築への野心を反映）。インストール：pip install claude-agent-sdk / npm install @anthropic-ai/claude-agent-sdk。認証：ANTHROPIC_API_KEY、またはBedrock/Vertex AI/Azure対応。組み込みツール：ファイル読み書き・コマンド実行・Web検索・コード編集が利用可能。カスタムツール追加の3方式：MCPサーバー、Claude-skill、関数宣言。Agent Teamsにより：Claude Codeインタラクティブモードとプログラマティックモード双方でマルチエージェント能力が利用可能。Managed Agentsパブリックベータ：セキュアサンドボックス・組み込みツール・SSEストリーミング付き完全マネージドエージェントハーネス。セルフホストサンドボックスパブリックベータ：ツール実行を自環境に移動しつつエージェントループはAnthropicインフラ上。Claude Agent SDKがフレームワークランキング2位（LangGraph次点）。
