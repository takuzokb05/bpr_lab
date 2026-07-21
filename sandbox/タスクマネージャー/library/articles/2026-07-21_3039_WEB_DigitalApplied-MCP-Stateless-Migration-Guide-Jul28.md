# MCP Goes Stateless July 28: What Breaks, What Gets Cheaper

- URL: https://www.digitalapplied.com/blog/mcp-2026-07-28-spec-stateless-migration-guide
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-21

## 投稿内容
Migration guide for the MCP 2026-07-28 specification release candidate. The biggest change is the stateless core: remote MCP servers no longer need sticky sessions, shared session stores, or deep packet inspection at the gateway—they can run behind plain round-robin load balancers. Covers: how to remove session management code, how to integrate new extensions (Tasks, MCP Apps), and how to migrate to the new OAuth/OIDC-aligned authorization. Also explains cost reduction from stateless architecture.

## 要約
2026-07-28 MCP仕様RC対応の移行ガイド。最大の変更はステートレスコアへの移行：スティッキーセッション・共有セッションストア・ゲートウェイDPI不要になりラウンドロビンLB対応可能に。セッション管理コードの削除方法、Tasks/MCP Apps拡張の組み込み方、OAuth/OIDCに準拠した新認証への移行手順を具体的に解説。ステートレス化によるスケーリングコスト削減効果も定量化。本番MCPサーバーを運用している開発者が7/28前に確認必須の実践的ガイド。
