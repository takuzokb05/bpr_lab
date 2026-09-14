# The 2026-07-28 MCP Specification: Stateless Core, Extensions & Auth Hardening

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-14

## 投稿内容
Official Model Context Protocol blog post announcing the final 2026-07-28 specification, the largest MCP revision since launch.

## 要約
MCP 2026-07-28最終仕様の公式ブログ解説（MCPローンチ以来最大改訂）。最大変更はプロトコル層のステートレス化：セッション概念・初期化ハンドシェイクを削除し通常HTTPで水平スケール可能に。主な新機能：①ステートレスコア（スケーラブルHTTP基盤）、②Multi Round-Trip Requests（長時間処理対応）、③ヘッダーベースルーティング、④キャッシュ可能なlistレスポンス、⑤OAuth/OpenID Connect準拠の認証強化（authorizationハードニング）、⑥拡張フレームワーク（MCP Apps：サーバーレンダリングUI・Tasksエクステンション：長時間処理ジョブ）。Tier 1 SDKs（TypeScript・Python）は月5億DL超・累計10億DL突破。RC提出：2026年5月21日、最終仕様：2026年7月28日。既存MCPサーバーの移行ガイドと破壊的変更一覧が含まれる。Claude Code/Agent SDKを使う場合のMCP設定への影響も解説。
