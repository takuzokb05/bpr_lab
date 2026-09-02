# MCP仕様「2026-07-28」を公開――プロトコルをステートレス化（gihyo.jp）

- URL: https://gihyo.jp/article/2026/07/mcp-spec-2026-07-28
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-09-02

## 要約
gihyo.jpによるMCP仕様2026-07-28公開の日本語解説記事：
- 最大の変更: プロトコルをステートレス化（セッションIDと初期化処理を廃止）
- 各リクエストが自己完結型（プロトコルバージョン・クライアント情報・対応機能を含む）
- クラウド展開が通常のHTTPワークロードと同等に（スケールアップが容易に）
- Multi Round-Trip Requests: 長時間処理に対応
- ヘッダーベースルーティング・キャッシュ可能リスト結果を追加
- 認可強化: OAuth/OpenIDConnectとの整合性を改善、Enterprise-Managed Authorizationが安定版に
- 正式な拡張機構（extensions framework）を導入
- MCP Apps: サーバーレンダリングUIの拡張
- Tier 1 SDKが更新済み、breaking changesを含む（最大の改訂）
