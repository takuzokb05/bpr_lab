# MCP 2026-07-28: ステートレスコア・ID-JAG認可・SDK Beta詳解（Fmind）

- URL: https://fmind.medium.com/mcp-2026-07-28-stateless-core-enterprise-authorization-and-sdk-betas-2646a980d594
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-14

## 要約
Fmind（ML Engineer）によるMCP 2026-07-28 RCの技術深掘り解説。主要変更：(1)ステートレスコア：initialize/initializedハンドシェイク廃止。クライアント情報・バージョン・ケイパビリティが全リクエストの_metaフィールドに埋め込まれ自己記述型に。ラウンドロビンLBがセッションアフィニティなしで動作可能。(2)新HTTPヘッダー：Mcp-Protocol-Version・Mcp-Method・Mcp-Nameでルーティング最適化。(3)多ターンツール：InputRequiredResult + opaque `requestState`トークンで複数ラウンドトリップが可能。(4)エンタープライズ認可：RFC 8693 Token ExchangeによるID-JAG（Identity Assertion JWT Authorization Grant）実装でSSO連携・インタラクティブ同意不要。SDK Beta状況：Python `mcp[cli]==2.0.0b1`・TypeScript `@modelcontextprotocol/server@beta`・Go `v1.7.0-pre.1`・C# prerelease。廃止宣言：Roots・Sampling・Loggingを12ヶ月移行期間付きで廃止。
