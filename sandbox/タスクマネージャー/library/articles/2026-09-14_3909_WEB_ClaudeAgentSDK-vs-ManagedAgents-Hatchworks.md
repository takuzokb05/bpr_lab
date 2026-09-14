# Claude Agent SDK vs Managed Agents: Where to Run Production Agents

- URL: https://hatchworks.com/blog/claude/claude-agent-sdk-and-managed-agents/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-14

## 投稿内容
Detailed comparison of Claude Agent SDK (self-hosted) and Managed Agents (Anthropic-hosted) for production deployments.

## 要約
Claude Agent SDK（ローカルホスト型）vs Managed Agents（Anthropicホスト型）の本番運用比較（Hatchworks）。Agent SDKはPython/TypeScriptライブラリでClaude Codeと同じエージェントループを自インフラで実行するもの。Managed Agents（2026年4月GA）はREST APIでAnthropicがサンドボックス/セッションログ/ハーネスを管理。Anthropic公式推奨：「プロトタイプ→Agent SDK、本番→Managed Agents」。Agent SDK が適するケース：CI/CD組み込み・既存インフラ統合・完全制御・長期間エージェント実行。Managed Agents が適するケース：長時間非同期タスク（1時間以上）・インフラ管理不要・組み込みサンドボックスが必要・スケール不確定。7種類の公式SDK（Python/TypeScript/Go/Java/C#/Ruby/PHP）でも同じ4ステップ（agent定義→実行環境→セッション開始→イベントストリーム）。FXシステムへの応用：定期分析バッチはAgent SDK、マルチステップ調査はManaged Agentsが適合。
