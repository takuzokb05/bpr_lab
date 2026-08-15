# MCP 2026-07-28 Goes Stateless: What Breaks and How to Migrate

- URL: https://mcpjam.substack.com/p/mcp-2026-07-28-goes-stateless-what
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-15

## 要約
MCPJam による MCP 2026-07-28 スペックの破壊的変更解説。ステートレス化の核心：「initialize/initialized ハンドシェイクの廃止」「Mcp-Session-Id の削除」「各リクエストへのプロトコルバージョン・クライアント情報・ケイパビリティの埋め込み」。移行ステップ：①隠れセッション状態の棚卸し → ②server/discover 実装 → ③ヘッダー・ボディパリティ検証 → ④list 結果の決定論的キャッシュ対応 → ⑤レガシーパスの並走 → ⑥ラウンドロビン・認証・リプレイテスト。重要な注意点：「ステートレスMCPはステートレスソフトウェアではない」— アプリ層の状態（承認フロー、セッションデータ）は引き続き明示的に管理が必要。SDK Beta（Python/TypeScript/Go/C#）で先行移行可能。
