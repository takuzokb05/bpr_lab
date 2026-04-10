# Scaling Managed Agents: Decoupling the Brain from Infrastructure（Anthropic Engineering）

- URL: https://www.anthropic.com/engineering/managed-agents
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-04-10

## 要約
Anthropic エンジニアリングブログによる Claude Managed Agents の技術解説。2026年4月8日に public beta 公開された Managed Agents の内部アーキテクチャを解説した一次情報。「Brain（LLM推論）とRuntime（セッション管理・サンドボックス）の分離」が設計の核心。API エンドポイントには managed-agents-2026-04-01 ベータヘッダーが必要。料金は通常のトークン料金＋$0.08/セッション時間＋$10/1,000 Web検索。YAML ファイルかナチュラルランゲージでエージェント定義、ガードレール設定、Anthropic インフラ上での完全ホスト実行を提供。既採用企業として Notion、Rakuten、Asana、Sentry が列挙されており、コードオートメーション・HR・財務ワークフローへの活用事例も紹介。
