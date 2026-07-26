# MCP Goes Stateless on Monday. Here's What Breaks and What to Do About It（Luke Oliff）

- URL: https://lukeocodes.dev/mcp-goes-stateless
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-26

## 要約

開発者Luke Olifによる実践的なMCPステートレス移行ガイド。7月28日に何が壊れるかと対処法を実例コードで解説。initialize ハンドシェイクと Mcp-Session-Id ヘッダーが削除されるため、既存のセッション管理コードはすべて修正が必要。各リクエストの _meta フィールドへのクライアント情報移行パターン、tools/list キャッシュ戦略、ステートを保持する必要があるサーバーの代替アーキテクチャ（拡張機能としてのTasksの利用）を詳述。「月曜日（7月28日）に使えるmigrationチェックリスト」形式で実用的。既存MCPサーバー開発者に直接役立つ移行手順書。
