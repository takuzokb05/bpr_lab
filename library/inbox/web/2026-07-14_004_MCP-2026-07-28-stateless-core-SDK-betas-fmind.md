# MCP 2026-07-28: ステートレスコア・エンタープライズ認可・SDK Beta

- URL: https://fmind.medium.com/mcp-2026-07-28-stateless-core-enterprise-authorization-and-sdk-betas-2646a980d594
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-14

## 要約
FmindによるMCP 2026-07-28 RC技術解説。主要変更：(1)ステートレスコア：initialize/initializedハンドシェイク廃止、クライアント情報・バージョン・ケイパビリティが全リクエストの_metaフィールドで送信。ラウンドロビンLBが可能に。(2)新HTTPヘッダー：Mcp-Protocol-Version・Mcp-Method・Mcp-Name。(3)多ターンツール呼び出し：InputRequiredResult+opaque requestStateトークンで実現。(4)企業認可：RFC 8693トークン交換によるID-JAG（Identity Assertion JWT Authorization Grant）でSSO連携。SDK Beta：Python mcp[cli]==2.0.0b1、TypeScript @modelcontextprotocol/server@beta、Go v1.7.0-pre.1、C# prerelease。廃止：Roots・Sampling・Logging（12ヶ月移行期間）。
