# The Register: MCP prepares to break with its stateful past (July 23)

- URL: https://www.theregister.com/devops/2026/07/23/model-context-protocol-prepares-to-break-with-its-stateful-past/5276722
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-27

## 投稿内容
The Register's in-depth technical analysis of MCP's 2026-07-28 specification rewrite, covering breaking changes and strategic implications for the protocol ecosystem.

## 要約
The Register（2026年7月23日）によるMCP 2026-07-28 RCの技術的分析。「ステートフルな過去と訣別」と題し批評的・技術的視点から分析。MCPが元々はローカルツールとして設計されたが重要な分散プロトコルになった経緯を解説。主な破壊的変更: ①セッション層の完全廃止（クライアントメタデータは全リクエストの`_meta`フィールドで送付）、②2つの必須HTTPヘッダー追加（`Mcp-Method`含む）、③エラーコード変更（クライアントコードがパターンマッチするコード変更）、④Completions/Roots/Sampling 3プリミティブの非推奨化。Anthropicの戦略的判断としてMCPをOpenAI Agents SDK・Google ADKと差別化する「デファクト標準」として押し上げようとしていると分析。Tier 1 SDK（TypeScript・Python）は4-6週間でサポート予定。The Registerらしい批評的かつ深度の高い技術解説記事。
