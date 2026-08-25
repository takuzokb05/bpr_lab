# MCP 2026-07-28 公式仕様リリース — ステートレスコア・Apps拡張・OAuth強化

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-25

## 要約
Model Context Protocol（MCP）の最新仕様 2026-07-28 が正式リリース。主要変更点：(1) ステートレスプロトコルコア—セッションストアや DPI 不要でラウンドロビンLBで動作可能に。(2) Multi Round-Trip Requests、ヘッダーベースルーティング、キャッシュ可能リスト結果。(3) OAuth/OIDCによる認証強化。(4) MCP Apps拡張—サーバーがReactダッシュボード等のUIコンポーネントをホストへプッシュ可能。(5) Tasks・サブスクリプション・進行通知の正式化。TypeScript/Python SDKともに10億ダウンロード超。Anthropic・Cloudflare・AWS等全主要ベンダーが採用。既存ステートフルサーバーからの移行はヘッダーベースセッション管理が推奨パス。
