# MCP Goes Stateless: What the 2026-07-28 Spec Breaks and Fixes for Server Authors

- URL: https://jsmanifest.com/mcp-stateless-spec-2026-07-28
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-05

## 要約
サーバー著者向けのMCP 2026-07-28仕様変更実践解説。何が壊れ何が改善されるかを具体的に説明。破壊的変更：①initialize/initializedハンドシェイク廃止（SEP-2575）、②Mcp-Session-Idヘッダー削除（SEP-2567）、③クライアント情報がリクエストの_metaに付与される方式に移行。改善点：①ロードバランサーのスティッキーセッション設定不要、②水平スケーリングが単純化、③OAuth 2.1/OIDCによる企業グレード認証確立。移行対応：セッション状態をサーバー側で管理していたサーバーは内部ストア移行が必要。10週間の検証ウィンドウ（〜2026-07-28）内での対応が推奨。
