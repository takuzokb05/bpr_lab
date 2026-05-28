# AWS MCP Server 一般提供開始: IAM制御・CloudTrail監査付きAWSサービスMCP統合

- URL: https://aws.amazon.com/blogs/aws/the-aws-mcp-server-is-now-generally-available/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-28

## 投稿内容
The AWS MCP Server is now generally available. AWS announced the general availability of the AWS MCP Server on May 6, 2026. A managed server that gives AI coding agents secure, auditable access to AWS services through the Model Context Protocol. Agents can now call any AWS API through a single tool, including operations that require file uploads or long-running execution. Sandboxed script execution lets agents run Python code against AWS services for multi-step operations. Available at no additional charge in US East (N. Virginia) and Europe (Frankfurt) AWS Regions.

## 要約
AWSが2026年5月6日にAWS MCP ServerのGA（一般提供）を開始。AIコーディングエージェントがModel Context Protocol経由でAWSサービスに安全・監査可能にアクセスできるマネージドサーバー。単一ツールでファイルアップロードや長時間実行を含む任意のAWS APIを呼び出し可能、Pythonコードのサンドボックス実行でマルチステップ操作に対応（ローカルFS・シェルツールへのアクセスなし）。IAMコンテキストキーで細粒度のアクセス制御を標準IAMポリシーで実現、個別の専用IAMパーミッション不要に。Amazon CloudWatch・AWS CloudTrailによる完全な監視・ログ記録。認証なしでドキュメント検索が可能に。追加料金なし（AWSリソース利用料のみ）。US East(N.Virginia)・EU(Frankfurt)リージョン提供、任意リージョンへのAPI呼び出し対応。Agent Toolkit for AWSの中核コンポーネントとして位置付け。
