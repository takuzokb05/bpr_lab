# MCP 2026-07-28: From Local Tool to Distributed Protocol — Migration Guide

- URL: https://aaif.io/blog/mcp-2026-07-28-whats-changing-and-how-to-migrate
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-08

## 要約
Agentic AI Foundation (AAIF)によるMCP 2026-07-28仕様の変更点と移行ガイド。今回仕様の最大の変更はプロトコルレベルのステートレス化：①セッションと初期化ハンドシェイクが廃止→水平スケーリングがシンプルに（スティッキーセッション不要）。②Multi Round-Trip Requests追加：長時間処理を複数往復で継続可能。③ヘッダーベースルーティング（Mcp-Methodヘッダー）：ゲートウェイでディープパケットインスペクション不要に。④listレスポンスのキャッシュ対応：tools/listをクライアントがキャッシュ可能。⑤認証強化とExtensionsフレームワーク正式化。⑥TypeScript/Python/Go/C# SDK同時更新。移行コスト：ステートフルサーバーはリファクタリング必要、ステートレスで設計済みなら追加コスト最小。MCPを「ローカルツール拡張」から「分散プロトコル」へ格上げした歴史的リリース。
