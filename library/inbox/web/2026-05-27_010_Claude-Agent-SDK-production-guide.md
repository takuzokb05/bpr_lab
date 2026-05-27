# Building Agents with the Claude Agent SDK (Official Anthropic Engineering Blog)

- URL: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-27

## 要約
Anthropic公式エンジニアリングブログによるClaude Agent SDK（旧Claude Code SDK）の公式ガイド。旧称「Claude Code SDK」から「Claude Agent SDK」にリネーム、コード生成を超えた汎用エージェント構築への野心を反映。SDKはPython・TypeScriptで提供（pip install claude-agent-sdk / npm install @anthropic-ai/claude-agent-sdk）、ANTHROPIC_API_KEYまたはBedrock/Vertex AI/Azure対応。Claude Codeと同じツール・エージェントループ・コンテキスト管理をプログラマティックに利用可能。組み込みツール（ファイル読み書き・コマンド実行・Web検索・コード編集）が使用可能。カスタムツールはMCPサーバーまたはClaude-skillまたは関数宣言の3方式で追加可能。Agent Teamsによりマルチエージェント能力がClaude Codeインタラクティブモードとプログラマティックモード双方で利用可能に。Managed Agentsパブリックベータではセキュアサンドボックス・組み込みツール・SSEストリーミングが提供。
