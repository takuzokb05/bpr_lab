# Claude Agent SDK × MCPサーバー実践接続ガイド：StreamableHTTP・OAuth 2.1対応版

- URL: https://team400.ai/blog/2026-03-claude-agent-sdk-mcp-servers-guide
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-17

## 要約
Claude Agent SDKとMCPサーバー接続の実践ガイド（2026年最新版）。重要変更点：Streamable HTTP（旧HTTP+SSE を置き換え）がクラウドホスト型MCPの標準トランスポートに確定、OAuth 2.1がリモートMCPサーバーの認証標準として採用。3種トランスポートの使い分け：ローカルプロセス（低レイテンシ）/ HTTP接続（スケーラブル）/ SDK内直接実行（テスト用）。GitHub・Slack・データベース接続のコードサンプル付き。Claude Code CLIでもDesktopと同一MCPサーバーを共有できる点を図解。カスタムツール実装不要でAPIを接続できる設計の詳細。
