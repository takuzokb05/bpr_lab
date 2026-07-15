# MCP Just Went Stateless: Azure App Service での 2026 仕様スケーリング実装（Microsoft Tech Community）

- URL: https://techcommunity.microsoft.com/blog/appsonazureblog/mcp-just-went-stateless-%E2%80%94-what-the-2026-spec-changes-about-scaling-on-app-servic/4530222
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-24

## 要約
Microsoft Tech CommunityによるAzure App Service視点でのMCPステートレス化実装ガイド。従来の問題：MCPサーバーはWebSocket/SSEでステートフルな接続を維持する必要があり、Azure App ServiceのスケールアウトでリクエストがWebSocketセッションを持たないインスタンスにルーティングされると接続断が発生。2026仕様での解決：ステートレスHTTPのみで動作するためAzure App Serviceの標準ロードバランサーをそのまま使用可能（スティッキーセッション設定不要）。認証統合：Entra IDでの認証フロー設定例付き。Rate Limits API連携でAzure API Managementとの組み合わせ方法も解説。Azureエコシステムを使うエンタープライズMCP導入の実践的な移行ガイドとして、Azure使用組織には必読の内容。
