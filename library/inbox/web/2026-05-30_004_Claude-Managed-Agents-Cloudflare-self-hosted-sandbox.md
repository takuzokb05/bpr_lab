# Claude Managed Agents on Cloudflare: 自己ホスト型サンドボックス・プライベートMCP統合

- URL: https://blog.cloudflare.com/claude-managed-agents/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-30

## 要約
CloudflareとAnthropicがClaude Managed AgentsとCloudflare Sandboxesの統合を発表。開発者はエージェントのツール実行環境を自社インフラまたはCloudflare管理プロバイダーに移行可能。主要機能：(1)軽量V8 isolatesサンドボックス（数ミリ秒ブート、従来VMより低コスト）、(2)カスタムプロキシによるエージェントトラフィック認証・管理、(3)MCP tunnelsでプライベートネットワーク内サービスへの安全接続、(4)Cloudflare Browser Runによるブラウザ操作（セッション記録・監査証跡付き）、(5)エージェント専用メールアドレスの提供。GitHubテンプレート（cloudflare/claude-managed-agents）で数分で起動可能。Code with Claude London 2026で発表されたSelf-hosted sandboxesパブリックベータの一環。「エージェントのための最もシンプルで安全で構成可能なクラウド」を標榜。
