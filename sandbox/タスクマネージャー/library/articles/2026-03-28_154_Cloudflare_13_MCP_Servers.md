# Thirteen New MCP Servers from Cloudflare (Cloudflare Blog)

- URL: https://blog.cloudflare.com/thirteen-new-mcp-servers-from-cloudflare/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-03-28

## 要約

CloudflareがリリースしたMCPサーバー13種の公式発表。特に重要なもの：
- **D1 MCP**: SQLiteベースのCloudflare D1データベースをClaude/AIエージェントから直接操作
- **R2 MCP**: オブジェクトストレージR2へのファイルアップロード・取得
- **KV Bindings MCP**: Key-Value ストアへのアクセス
- **Container MCP**: Claude（claude.ai等）が実行環境を持たない場合に、**サンドボックス化された実行環境**を提供するサーバー。Claudeがリアルタイムでコマンド実行・仮説検証が可能になる
- Documentation MCP: Cloudflareドキュメントの意味検索

Container MCPは「実行環境なしのクライアント」の課題を解決する重要なアーキテクチャ。
