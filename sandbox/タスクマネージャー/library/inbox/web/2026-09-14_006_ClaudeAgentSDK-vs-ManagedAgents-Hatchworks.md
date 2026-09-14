# Claude Agent SDK and Managed Agents: Where to Run Production Agents

- URL: https://hatchworks.com/blog/claude/claude-agent-sdk-and-managed-agents/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-14

## 要約
Claude Agent SDK（ローカルホスト型）とClaude Managed Agents（Anthropicホスト型）の使い分けを詳細比較。Agent SDKはPython/TypeScriptライブラリでClaude Codeと同じエージェントループを自インフラで動かすもの。Managed AgentsはREST APIでAnthropicがサンドボックス・セッションログ・ハーネスを管理するもの（2026年4月リリース）。Anthropic公式の推奨は「プロトタイプ→Agent SDK、本番→Managed Agents」。Agent SDKが適するケース：CI/CD組み込み、既存インフラ統合、完全制御が必要な場合。Managed Agentsが適するケース：長時間非同期タスク、インフラ管理不要、組み込みサンドボックスが必要な場合。7種類の公式SDK（Python/TypeScript/Go/Java等）でも同様の4ステップ（agent定義→実行環境→セッション開始→イベントストリーム）で開始可能。
