# MCP 2026-07-28 Goes Stateless: What Breaks and How to Migrate

- URL: https://mcpjam.substack.com/p/mcp-2026-07-28-goes-stateless-what
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-15

## 要約
MCPJam (Substack) による MCP 2026-07-28 スペックの破壊的変更解説。ステートレス化の核心は「initialize/initialized ハンドシェイクの廃止」「Mcp-Session-Id の削除」「各リクエストへのプロトコルバージョン・クライアント情報・ケイパビリティの埋め込み」。移行ステップ：隠れセッション状態の棚卸し → server/discover 実装 → ヘッダー・ボディパリティ検証 → list 結果の決定論的キャッシュ対応 → レガシーパスの並走 → ラウンドロビン・認証・リプレイテスト。アプリケーション状態（ショッピングカート、承認フロー等）はまだ必要であり「ステートレスMCPはステートレスソフトウェアではない」という重要な注意点も示す。
