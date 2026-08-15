# MCP is now stateless: what the 2026-07-28 update changes

- URL: https://flaviocopes.com/mcp-2026-07-28-stateless/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-15

## 要約
Flavio Copes による MCP ステートレス化の平易な解説。ステートレス化で何が楽になるか：ラウンドロビンLBの直接適用可能、サーバーレス・エッジへのデプロイ、スティッキーセッション不要、ゲートウェイでのディープパケットインスペクション不要。何が変わらないか：アプリロジック層の状態管理は引き続き必要。旧スペック(initialize handshake)と新スペック(Mcp-Method ヘッダーベース)の対比コード例付き。MCPJam 記事と相補的な入門向け解説。開発者が移行前に読む最短コースとして機能する。
