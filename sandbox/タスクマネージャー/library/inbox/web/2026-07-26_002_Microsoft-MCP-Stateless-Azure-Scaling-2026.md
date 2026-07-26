# MCP Just Went Stateless — What the 2026 Spec Changes About Scaling on Azure App Service（Microsoft Community Hub）

- URL: https://techcommunity.microsoft.com/blog/appsonazureblog/mcp-just-went-stateless-%E2%80%94-what-the-2026-spec-changes-about-scaling-on-app-servic/4530222
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-26

## 要約

MicrosoftがAzure App ServiceにおけるMCPステートレス化の影響を解説。従来は sticky session・共有セッションストア・ディープパケットインスペクションが必要だったリモートMCPサーバーが、今後は通常のラウンドロビン型ロードバランサーで動作可能になる。Mcp-Method ヘッダーでトラフィックをルーティング、tools/list レスポンスをクライアントでキャッシュできるようになり運用コストが大幅削減。Azure App ServiceのMCP対応構成への具体的な移行手順と注意点を解説。エンタープライズMCPデプロイの標準構成が変わる可能性を指摘。
