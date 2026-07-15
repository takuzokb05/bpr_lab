# MCP Spec Ships July 28 — Every Breaking Change and How to Migrate

- URL: https://dev.to/akaranjkar08/mcp-spec-ships-july-28-every-breaking-change-and-how-to-migrate-4co8
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-06

## 要約
Dev.to の実装者向け記事。MCP 2026-07-28 仕様の全破壊的変更と具体的な移行手順を解説。ステートレス化により各リクエストの _meta フィールドに protocol_version・client_info・capabilities を含める必要がある。MCP Apps（SEP-1865）でサーバーが HTML UI を提供できるようになり、ホストがサンドボックス iframe でレンダリング。Tasks（SEP-1492）で長時間非同期処理のトラッキングが可能に。開発者が取るべき移行ステップを段階的に説明しており、既存サーバー運営者にとって実践的な参照資料。10週間の検証ウィンドウ（7/28まで）を活用することを推奨。
