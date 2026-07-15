# MCPビルダーが7月までに知るべきこと：2026-07-28仕様移行ガイド

- URL: https://www.gravitee.io/blog/what-every-mcp-builder-needs-to-know-before-july
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-25

## 要約
API管理企業Graviteeによる2026-07-28 MCP仕様RC発表を受けた実装者向け移行ガイド。
移行で必要な対応：
- **セッション管理コード削除**：Mcp-Session-Idヘッダとinitializeハンドシェイクへの依存を除去
- **リクエストごとの_meta実装**：プロトコルバージョン・クライアント情報をすべてのリクエストに添付
- **OAuth/OIDCスコープの設定**：ツール・リソースレベルの細粒度権限設計
- **負荷分散設定の変更**：スティッキーセッション不要になるためround-robin LBに対応
- **server/discoverメソッド対応**：オンデマンドなケイパビリティ取得に対応
移行期間は5月21日RC公開〜7月28日ファイナル（約10週間）。Tier-1 SDK実装者向け検証ウィンドウ。MCP利用者・開発者に必須の実践情報。
