# Claude Agent SDK and Managed Agents: Where to Run Production Agents

- URL: https://hatchworks.com/blog/claude/claude-agent-sdk-and-managed-agents/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-05

## 投稿内容
HatchworksによるClaude Agent SDKとManaged Agentsのプロダクション比較。Managed Agents（Cloudflare経由）: Anthropicインフラ上でエージェントループを実行、インフラ管理不要。Self-hosted via SDK: 自社ネットワークポリシー・監査ログ・セキュリティツール適用可能なサンドボックス（パブリックベータ）。MCPトンネル（リサーチプレビュー）でプライベートネットワーク内MCPサーバーへの安全アクセスが可能。セキュリティ要件・スケーリング要件・コストの3軸での選択基準と実装パターンを詳解。

## 要約
Claude AgentのManaged（Cloudflare）vs Self-hosted SDK選択基準と実装ガイド。新機能: Self-hosted Sandbox（パブリックベータ）で自社ネットワークポリシー・監査ログ適用、MCPトンネル（リサーチプレビュー）でプライベートネット内MCPサーバーに安全接続。選択軸：インフラ管理不要→Managed、セキュリティ・コンプライアンス要件あり→Self-hosted。FX取引エージェントのような機密性の高いシステムはSelf-hosted sandboxが適切な選択肢。
