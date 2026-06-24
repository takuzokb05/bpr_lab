# MCP Goes Stateless: The 2026 Release Candidate Explained - ByteIota

- URL: https://byteiota.com/mcp-goes-stateless-2026-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-24

## 要約
ByteIotaによるMCP 2026-07-28リリース候補の詳細解説。最大の変更点：ステートレスプロトコルコアへの移行。initialize/initializedハンドシェイク廃止、Mcp-Session-Idヘッダー削除、クライアント情報・capabilities をリクエストの_metaフィールドに埋め込む方式に変更。効果：ラウンドロビン負荷分散がスティッキーセッションなしで機能、水平スケーリングが容易に。アプリケーション状態はbasket_idのような明示的ハンドル経由で管理。RootsとSamplingとLoggingが非推奨化（12ヶ月の猶予期間）。7月28日に最終仕様公開予定。
