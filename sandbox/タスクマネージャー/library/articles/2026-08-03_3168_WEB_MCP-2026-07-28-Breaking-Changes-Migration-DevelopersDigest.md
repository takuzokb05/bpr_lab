# The MCP 2026-07-28 Rewrite: What Breaks and How to Migrate

- URL: https://www.developersdigest.tech/blog/mcp-2026-07-28-breaking-changes
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-03

## 要約
MCP 2026-07-28仕様の破壊的変更点と移行ガイドを解説した技術記事（Developers Digest）。既存MCPサーバーの移行作業に必須の実践情報。

**主要な破壊的変更**:
1. **initialize/initializedハンドシェイクの削除**：接続フローが大幅に簡略化
2. **Mcp-Session-IdヘッダーからMcp-Methodヘッダーベースルーティングへ移行**
3. **ステートレスプロトコルコアの採用**：サーバーがスティッキーセッション・共有セッションストア不要に

**メリット**:
- リモートMCPサーバーが普通のラウンドロビンロードバランサーで運用可能に（スケーリングコスト大幅削減）
- Cloudflare Workers・Vercel Functionsなど汎用WebサーバーでMCPサーバーが動作

**追加機能**:
- Multi Round-Trip Requests対応
- キャッシュ可能なtools/listレスポンス（ttlMsで有効期間指定）
- Authorization強化
- 拡張フレームワーク（Tier 1 SDKsも更新済み）

既存コードの具体的な修正箇所と移行手順を含む。本番環境のMCPサーバーをお持ちの方は早急に確認推奨。
