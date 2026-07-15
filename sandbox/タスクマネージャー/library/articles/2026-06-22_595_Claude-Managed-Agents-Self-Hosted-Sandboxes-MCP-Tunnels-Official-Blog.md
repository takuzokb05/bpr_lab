# Claude Managed Agents: Self-Hosted Sandboxes & MCP Tunnels（公式発表）

- URL: https://claude.com/blog/claude-managed-agents-updates
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-22

## 投稿内容
New in Claude Managed Agents: self-hosted sandboxes and MCP tunnels. On May 19, 2026 at Code with Claude in London, Anthropic shipped two new infrastructure options: self-hosted sandboxes (public beta) and MCP tunnels (research preview). Self-hosted sandboxes let companies run agent tool calls on their own infrastructure or through managed providers (Cloudflare, Daytona, Modal, Vercel). MCP tunnels connect agents to private network MCP servers without exposing them to the public internet.

## 要約
2026年5月19日、ロンドン「Code with Claude」開発者カンファレンスにてAnthropicが発表した2大エンタープライズインフラ機能。①**セルフホストサンドボックス（パブリックベータ）**: ツール実行を自社インフラまたはCloudflare・Daytona・Modal・Vercelで処理。エージェントループ（オーケストレーション・コンテキスト管理・エラーリカバリ）はAnthropicに残し、ツール実行のみ自社環境へ。②**MCPトンネル（リサーチプレビュー）**: 軽量ゲートウェイが単一アウトバウンド接続（E2E暗号化）を開設、インバウンドFW変更不要。社内Confluence・プライベートGitLab・オンプレDBへの安全接続が実現。企業がAIエージェントを運用しながら機密データ・ツール実行・内部システムを自社セキュリティ境界内に維持する基盤を整備。一次情報：Anthropic公式ブログ。
