# MCP Protocol Updates 2026: 9つの仕様変更とRCマイグレーションマップ（TokenMix）

- URL: https://tokenmix.ai/blog/mcp-updates-changelog-every-protocol-change-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-24

## 要約
TokenMixによるMCP 2026仕様変更の全変更点チェンジログ（移行マップ付き）。9つの主要変更をbefore/after形式で整理：①ハンドシェイク廃止（initialize/initializedフローなし）、②Mcp-Session-Idヘッダー削除、③_metaフィールド追加（プロトコルバージョン・クライアント情報を各リクエストに含む）、④Extensions framework（reverse-DNS ID: com.example.ext-feature方式、ext-*リポジトリで独立バージョニング）、⑤Tasks extension（tasks/get・tasks/update・tasks/cancel操作でLLMが非同期タスクを管理）、⑥MCP Apps（初の公式Extension）、⑦Roots非推奨、⑧Sampling非推奨、⑨Logging非推奨。移行優先度：まずSession ID依存コードを削除→_meta対応→deprecated機能の代替実装。Tier 1 SDK（Python・TypeScript）は10週間以内（〜9月上旬）に対応完了予定。MCPサーバー開発者向け最も実用的な移行ガイド。
