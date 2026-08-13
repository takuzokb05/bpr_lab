# MCP Just Went Stateless: What Changes for Your Servers (DigitalApplied)

- URL: https://www.digitalapplied.com/blog/mcp-2026-07-28-stateless-spec-agent-infrastructure-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-13

## 要約
DigitalApplied.comによるMCP 2026-07-28仕様の「ステートレス化」が既存サーバーインフラに与える影響の詳細技術分析。最大の変更点：initialize ハンドシェイク廃止・Mcp-Session-Idヘッダー廃止・server-initiated requestsをリトライパターンに置換。この変更でサーバーレスデプロイ・エッジ配信が可能になりスケールアップが容易に。既存ステートフルサーバーの移行手順を具体的に解説。Python SDK 2.0同時リリース（主要クラス名変更あり）。Tier 1 SDK（Python/TypeScript/Java/C#）すべてが対応済み。Rustは対応ベータ版。
