# Anthropic Introduces MCP Tunnels for Private Agent Access to Internal Systems

- URL: https://www.infoq.com/news/2026/05/claude-mcp-tunnels/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-22

## 要約
InfoQによるClaude MCP Tunnels発表の技術報道（2026年5月）。**技術的詳細**: MCPトンネルは軽量ゲートウェイが単一アウトバウンド接続（エンドツーエンド暗号化）を開設する設計。インバウンドファイアウォールルール変更不要・パブリックエンドポイント不要。エンタープライズVPNやゼロトラストネットワーク環境でもデプロイ可能。**利用シナリオ**: 社内Confluenceへのアクセス、プライベートGitLabサーバー、オンプレミスDBへのMCP接続。**ステータス**: リサーチプレビュー、アクセスリクエスト必要。セルフホストサンドボックスはパブリックベータ（Cloudflare Workers/Daytona/Modal/Vercel対応）。**セキュリティ強化の背景**: 2026年4月に14件のCVE（MCPサーバー経由RCE）が報告されたことを受け、プライベートネットワーク内でのセキュアな接続手段の需要が高まっている。**対応必要事項**: AWS PrivateLink/Azure Private Endpointとの組み合わせで完全プライベート環境を実現可能。
