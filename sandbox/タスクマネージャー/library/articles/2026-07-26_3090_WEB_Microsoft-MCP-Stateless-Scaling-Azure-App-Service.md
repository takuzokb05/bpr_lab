# MCP Just Went Stateless — What the 2026 Spec Changes About Scaling on Azure App Service

- URL: https://techcommunity.microsoft.com/blog/appsonazureblog/mcp-just-went-stateless-%E2%80%94-what-the-2026-spec-changes-about-scaling-on-app-servic/4530222
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-26

## 投稿内容

MicrosoftがAzure App ServiceにおけるMCPステートレス化の実務的影響を解説。Azure上でのMCPサーバー運用パターンが根本から変わることを示した公式解説。

## 要約

- 従来のリモートMCPサーバーに必要だったスティッキーセッション・共有セッションストア・ディープパケットインスペクションが不要になる
- Mcp-Method ヘッダーでトラフィックルーティングが可能になり、普通のロードバランサー構成で運用できる
- tools/list レスポンスをクライアントサイドでキャッシュできるようになるため、リクエスト数が削減されコスト低下
- Azure App Serviceの具体的な移行手順と注意点を提供（Auto Scalingとの相性、セッション削除後のエラーハンドリング等）
- ステートレス化により水平スケールが容易になり、エンタープライズレベルのMCP展開が実現可能に
- 既存のステートフル MCPサーバーからの移行パスも解説（段階的移行・Feature Flagの活用）
- AzureでのMCP本番運用を検討している開発者・アーキテクト向けの一次資料として価値が高い
