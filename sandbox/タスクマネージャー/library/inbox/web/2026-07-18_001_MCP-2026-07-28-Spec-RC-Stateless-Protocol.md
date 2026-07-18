# MCP 2026-07-28 仕様リリース候補：ステートレス化・拡張フレームワーク

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-18

## 要約
Model Context Protocol の2026年最大の仕様改定RC（リリース候補）が公開。「プロトコル開始以来最大の改訂」と銘打たれ、7月28日に最終版リリース予定。最大の変更はプロトコル層のステートレス化（SEP-2575/SEP-2567）：initialize/initialized ハンドシェイクの廃止、Mcp-Session-Id ヘッダの削除により、スティッキーセッション不要のラウンドロビンLB運用が可能に。新機能として拡張フレームワーク（SEP-2133：リバースDNS識別子、独立バージョニング）、Tasks拡張（ハンドル＋tasks/get/update/cancel）、W3C Trace Context伝播（SEP-414：分散トレーシング対応）が追加。10週間の移行ウィンドウが設けられており、プロダクション環境のMCPサーバー運用者は今すぐ対応着手が必要。
