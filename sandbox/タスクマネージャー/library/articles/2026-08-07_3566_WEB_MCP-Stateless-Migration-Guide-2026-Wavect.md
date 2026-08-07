# MCP Goes Stateless: Server Migration Guide 2026 — Wavect

- URL: https://wavect.io/blog/mcp-stateless-server-migration-2026/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-07

## 要約

MCP 2026-07-28仕様移行のための実装者向けステップバイステップガイド。

**移行前に実施するインベントリ**:
1. セッションIDに依存しているコードをgrepで全特定
2. `initialize`ハンドシェイクの呼び出し箇所
3. `Mcp-Session-Id`ヘッダーを送受信しているコード
4. サーバー側でセッション状態を保持しているデータストア

**移行手順（6ステップ）**:
1. `server/discover`エンドポイントを追加
2. 各リクエストヘッダーとボディのパリティ検証を追加
3. `tools/list` / `resources/list`の結果を決定論的かつキャッシュ対応に
4. `_meta`フィールドでprotocol version, client identity, capabilitiesを受け取る
5. テスト: conformance, authorization, replayおよびround-robinテスト
6. 旧インフラを最低12ヶ月維持（クライアント移行期間）

**廃止予定機能の扱い**:
- roots, sampling, loggingは廃止予定だが最低12ヶ月は維持必須
- 段階的廃止のSunset-Atヘッダーを返す実装を推奨

**よくある落とし穴**:
- セッションごとに異なる`tools/list`を返すと新仕様クライアントがキャッシュを壊す
- OAuth実装をMCP仕様の認証要件（DPoP, PKCE必須）に合わせる

**なぜ重要か**: MCPサーバーを自作・運用している場合の実務的移行手引き。
