# MCP 2026-07-28: From Local Tool to Distributed Protocol — Migration Guide

- URL: https://aaif.io/blog/mcp-2026-07-28-whats-changing-and-how-to-migrate
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-25

## 要約
AAIF（Agentic AI Foundation）によるMCP 2026-07-28仕様への移行ガイド。主要変更点と移行手順：(1) ステートレスコア移行—セッションIDをHTTPヘッダーに移動、サーバー側セッションストレージ不要に。既存コードの変更箇所：セッション初期化ロジックの削除、ヘッダーパースの追加。(2) OAuth/OIDC対応—新しいsecurity_schemesフィールドで認証方式を宣言。(3) MCP Apps拡張—サーバーがUI要素をプッシュする場合はapps_config設定が必要。(4) Tier 1 SDK（TypeScript/Python）はv3.0+で自動対応—既存SDK利用者は依存関係を更新するだけでほぼ完了。後方互換性：旧クライアントは引き続きサポートされるが新機能は利用不可。本番環境移行は段階的移行（カナリアリリース）を推奨。
