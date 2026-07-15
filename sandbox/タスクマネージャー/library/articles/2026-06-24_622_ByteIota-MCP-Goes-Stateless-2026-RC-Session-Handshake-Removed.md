# MCP Goes Stateless: 2026リリース候補の全変更点詳解（ByteIota）

- URL: https://byteiota.com/mcp-goes-stateless-2026-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-24

## 要約
ByteIotaによるMCP 2026-07-28リリース候補の技術詳細解説。最大の変更点はステートレスプロトコルコアへの移行。具体的変更：①initialize/initializedハンドシェイク廃止（プロトコルレベルのセッション確立不要に）、②Mcp-Session-Idヘッダー削除（スティッキーセッション不要）、③クライアント情報・capabilitiesを各リクエストの_metaフィールドに埋め込む形式に変更。インフラ効果：ラウンドロビン負荷分散がスティッキーセッションなしで機能、水平スケーリングが大幅に容易に。アプリケーション状態の管理方法：basket_idのような明示的ハンドルをtool経由で発行し、モデルが後続リクエストに引数として渡す。非推奨化：Roots・Sampling・Loggingが非推奨（Feature Lifecycle Policy: Active→Deprecated→Removed、各段階12ヶ月猶予）。MCP Apps（初の公式Extension）も同時追加。最終仕様は2026年7月28日公開予定、Tier 1 SDKは10週間以内に対応予定。
