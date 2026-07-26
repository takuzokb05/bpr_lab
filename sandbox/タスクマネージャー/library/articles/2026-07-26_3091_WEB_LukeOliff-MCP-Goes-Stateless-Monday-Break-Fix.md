# MCP Goes Stateless on Monday. Here's What Breaks and What to Do About It

- URL: https://lukeocodes.dev/mcp-goes-stateless
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-26

## 投稿内容

開発者Luke Olifによる実践的なMCPステートレス移行ガイド。7月28日に何が壊れるかをコードレベルで示し、before/after の修正例を提供。

## 要約

- initialize ハンドシェイクと Mcp-Session-Id ヘッダーが削除されるため、既存のセッション管理コードはすべて修正が必要
- 各リクエストに _meta.protocolVersion と _meta.clientInfo を付与する新パターンを before/after コードで解説
- tools/list をクライアント側でキャッシュする実装例を TypeScript で提示
- ステートを保持する必要があるサーバーは MCP Tasks 拡張を使って長時間実行タスクを管理する代替アーキテクチャを採用
- エラーコード変更（-32002→-32602）に対応するエラーハンドリングの修正も必要
- 「7月28日に使えるmigrationチェックリスト」形式で実用的
- 既存MCPサーバー保守者向けの実践的な移行手順書として価値が高い
