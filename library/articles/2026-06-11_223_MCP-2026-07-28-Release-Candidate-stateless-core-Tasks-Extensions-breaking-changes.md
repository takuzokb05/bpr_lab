# MCP 2026-07-28 仕様RC：ステートレス化・Tasks・認可強化・breaking changes

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-11

## 要約
Model Context Protocol公式ブログによる2026-07-28仕様リリース候補の発表。最終仕様は2026年7月28日公開予定。プロトコル史上最大の改訂で主要変更点は以下の通り。

**ステートレス化**：初期化ハンドシェイクとセッションIDを廃止。従来は粘性ルーティング・共有セッションストア・深いパケット検査が必要だったリモートMCPサーバーが、通常のHTTPラウンドロビンロードバランサーで動作可能になった。`Mcp-Method`ヘッダーで経路制御し、`tools/list`レスポンスはクライアント側でキャッシュ可能。

**拡張フレームワーク（Extensions）**：MCP Apps（サーバーレンダリングUI）とTasksエクステンション（長時間非同期タスク）が公式拡張として追加。

**認可強化**：OAuth 2.0/OpenID Connectとの整合性を向上。より既存のIDプロバイダーインフラに自然に統合可能に。

**非推奨化**：Roots・Sampling・Loggingを将来廃止予定として明示。正式なdeprecation policyを導入。

**Breaking changes**：エラーコード変更（-32002→-32602）、`tools/list`のJSON Schema対応。既存のサーバー・クライアント実装は互換性確認が必須。
