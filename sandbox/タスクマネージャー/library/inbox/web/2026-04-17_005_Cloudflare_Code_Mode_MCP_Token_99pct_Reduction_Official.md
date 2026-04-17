# Cloudflare Code Mode MCP: 2500+APIエンドポイントのトークン消費99.9%削減

- URL: https://blog.cloudflare.com/code-mode-mcp/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-04-17

## 要約
CloudflareがCode ModeをMCPサーバーとして提供開始。2,500以上のAPIエンドポイントとのやり取りに必要なコンテキストを1.17Mトークン→約1,000トークンに99.9%削減。仕組み：search()とexecute()の2ツールのみを公開。search()でOpenAPI仕様をプロダクトエリア・パス・メタデータで検索（仕様自体はコンテキストに入らない）、execute()でV8 isolate内のJavaScriptを安全実行しペジネーション・条件分岐・連鎖APIコールを1サイクルで処理。エンタープライズ版では全接続MCPサーバーをportal_codemode_searchとportal_codemode_executeの2ツールに集約。AIエージェントが複数のMCPサーバーを効率的に活用する際のトークンボトルネック解消に有効。InfoQ記事でも「AIエージェントが大規模APIを低コストで活用できる重要なインフラ進化」として紹介。MCP v2.1.127対応。
