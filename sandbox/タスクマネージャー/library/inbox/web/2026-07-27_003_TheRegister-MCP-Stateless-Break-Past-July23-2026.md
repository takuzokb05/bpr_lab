# Model Context Protocol prepares to break with its stateful past

- URL: https://www.theregister.com/devops/2026/07/23/model-context-protocol-prepares-to-break-with-its-stateful-past/5276722
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-27

## 要約
The Register（2026年7月23日）によるMCP 2026-07-28 RC仕様の技術的分析。「ステートフルな過去と訣別する」と題し、MCPが本来はローカルツールとして設計されたが今や重要な分散プロトコルになったことを指摘。主な破壊的変更: ①セッション層の完全廃止（クライアントメタデータは全リクエストの`_meta`フィールドで送付）、②2つの必須HTTPヘッダー追加、③エラーコードの変更、④Completions/Roots/Sampling 3つのプリミティブの非推奨化。Anthropicの戦略的判断としてMCPをOpenAI Agents SDK・Google ADKと差別化する「デファクト標準」として押し上げようとしていると分析。実装者向けの移行タイムライン（Tier 1 SDK: 4-6週間、コミュニティSDK: 10週間以内）も解説。The Registerらしい批評的かつ技術深度の高い視点が特徴。
