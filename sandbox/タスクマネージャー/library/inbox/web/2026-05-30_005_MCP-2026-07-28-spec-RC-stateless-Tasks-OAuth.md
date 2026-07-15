# MCP 2026-07-28仕様リリース候補: ステートレス化・Tasks拡張・OAuth強化

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-30

## 要約
MCP（Model Context Protocol）の次期仕様リリース候補が2026年5月21日に確定し、最終版は2026年7月28日公開予定。ローンチ以来最大の改訂で、(1)ステートレスプロトコル化：プロトコルレベルのセッション削除によりスティッキーセッション・共有セッションストア不要、通常のラウンドロビンHTTPロードバランサーで運用可能に、(2)拡張機能の正式化：Tasks拡張（実験的→Extension昇格）とMCP Apps（サーバーレンダリングUI）追加、(3)認可強化：OAuth 2.0/OpenID Connectとの整合改善、(4)廃止予定：Roots・Sampling・Loggingに12ヶ月以上の移行期間付きで非推奨化、(5)正式廃止ポリシー：プロトコルが後方互換を壊さず進化できるフレームワーク確立。RC確定から最終版まで10週間のSDK検証・適合テスト期間を設定。97M月間SDKダウンロード・5000本超サーバーエコシステムに影響。
