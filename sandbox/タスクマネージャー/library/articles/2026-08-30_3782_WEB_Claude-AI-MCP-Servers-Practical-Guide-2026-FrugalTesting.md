# Claude AI and MCP Servers: The Developer's Practical Guide for 2026

- URL: https://www.frugaltesting.com/blog/claude-ai-and-mcp-servers-the-developers-practical-guide-for-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-30

## 投稿内容

The Model Context Protocol 2026-07-28 release candidate includes a stateless protocol core, Extensions framework, Tasks, MCP Apps, authorization hardening, and a formal deprecation policy. MCP now has over 9,700 million monthly SDK downloads and 86,000+ GitHub stars. You can now restrict which sites a Claude Managed Agents agent's web_search and web_fetch tools can reach by setting allowed_domains or blocked_domains. The Skills API and the Files API are also available through Microsoft Foundry.

## 要約

開発者向けClaude AI × MCPサーバー実践ガイド2026（FrugalTesting）。主要トピック：
1. **MCP 2026-07-28仕様の破壊的変更**: ステートレスプロトコルコアへ転換（従来の双方向ステートフル → リクエスト/レスポンス型）。ラウンドロビンLB対応、Mcp-Methodヘッダーでルーティング、toolsリストをtlsMs期間クライアントキャッシュ可能に
- **エコシステム規模**: 月間SDK Downloads 97億回超・GitHubスター86,000+。Linux Foundation傘下Agentic AI Foundationが統治
2. **Managed Agents新機能**: allowed_domains/blocked_domainsでweb_search・web_fetchが参照できるサイトをAIエージェントベースで制限可能
3. **クラウド展開**: Skills API・Files APIがMicrosoft Foundry経由で利用可能。Google Cloud Vertex AIにcomputer use・browser useが近日対応
4. **SDK対応状況**: 4大Tier1 SDK（Python・TypeScript・Java・.NET）が2026-07-28仕様に全対応済み
