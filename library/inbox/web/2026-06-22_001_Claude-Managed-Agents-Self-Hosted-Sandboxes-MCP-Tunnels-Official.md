# New in Claude Managed Agents: Self-Hosted Sandboxes and MCP Tunnels

- URL: https://claude.com/blog/claude-managed-agents-updates
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-22

## 要約
2026年5月19日、ロンドン「Code with Claude」開発者カンファレンスにてAnthropicが発表。Claude Managed Agentsに2つの新インフラオプションを追加。①**セルフホストサンドボックス（パブリックベータ）**: エージェントのツール実行を自社インフラまたはCloudflare・Daytona・Modal・Vercelなどマネージドプロバイダー上で実行可能。エージェントループ（オーケストレーション・コンテキスト管理・エラーリカバリ）はAnthropicインフラ上に残し、ツール実行のみ企業内環境へ移動。②**MCPトンネル（リサーチプレビュー）**: プライベートネットワーク内のMCPサーバーへ、パブリックインターネット露出なしに接続。軽量ゲートウェイが単一アウトバウンド接続（エンドツーエンド暗号化）を開設し、インバウンドファイアウォールルール不要。企業が機密データ・ツール実行・内部システムアクセスを自社セキュリティ境界内に維持しながらAIエージェントを運用するための基盤整備。一次情報：Anthropic公式ブログ。
