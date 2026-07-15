# MCP Spec Ships July 28: Every Breaking Change and How to Migrate

- URL: https://dev.to/akaranjkar08/mcp-spec-ships-july-28-every-breaking-change-and-how-to-migrate-4co8
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-06

## 投稿内容
Dev.to の実装者向け記事。MCP 2026-07-28 仕様の全破壊的変更と具体的な移行手順。ステートレス化により各リクエストの _meta フィールドに protocol_version・client_info・capabilities を含める必要がある。MCP Apps（SEP-1865）でサーバーがHTML UI をホスト側に提供、サンドボックスiframeでレンダリング。Tasks（SEP-1492）で長時間非同期処理のトラッキングが可能に。10週間の検証ウィンドウ（7/28まで）を活用することを推奨。段階的移行手順と実装チェックリストを提供。

## 要約
Dev.to の実装者向けMCP移行ガイド。ステートレス化により各リクエストの _meta フィールドに protocol_version・client_info・capabilities を含める必要がある。MCP Apps（SEP-1865）でサーバーがインタラクティブ HTML UI をホスト側に提供できるようになり、新エコシステムの可能性を開く。Tasks（SEP-1492）で長時間非同期処理のトラッキングが標準化。具体的な移行コード例と段階的手順を提供。10週間の検証ウィンドウ（7/28まで）内での対応を推奨。
