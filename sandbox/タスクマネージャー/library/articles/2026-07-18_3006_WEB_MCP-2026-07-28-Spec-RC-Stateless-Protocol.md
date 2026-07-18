# MCP 2026-07-28 仕様RC：ステートレス化・拡張フレームワーク導入

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-18

## 投稿内容
Model Context Protocolの2026年最大の仕様改定リリース候補（RC）が公開。最終版は7月28日にリリース予定。「プロトコル開始以来最大の改訂」と銘打たれる。

主要変更点：
- **ステートレス化**（SEP-2575/SEP-2567）：initialize/initializedハンドシェイクとMcp-Session-Idヘッダを廃止。スティッキーセッション・共有セッションストアなしでラウンドロビンLBで動作可能に
- **拡張フレームワーク**（SEP-2133）：リバースDNS識別子・extensions mapによる独立バージョニング
- **Tasks拡張**：tools/callからタスクハンドルを返し、tasks/get/update/cancelでクライアントが駆動
- **W3C Trace Context伝播**（SEP-414）：traceparent/tracestate/baggageによる分散トレーシング対応

移行ウィンドウ：RC公開から10週間（移行のタイムラインとして機能）。

## 要約
MCPプロトコル最大の改訂RCが公開（最終版7/28）。最大変更はステートレス化：セッションIDとハンドシェイクを廃止し、LB構成が大幅簡素化。拡張フレームワーク・Tasks拡張・分散トレーシング対応も追加。14,000以上サーバー・9,700万DLのエコシステムにとって重要な移行作業が必要。Claude CodeのMCPサーバー開発者は10週間の移行ウィンドウ内での対応が推奨される。
