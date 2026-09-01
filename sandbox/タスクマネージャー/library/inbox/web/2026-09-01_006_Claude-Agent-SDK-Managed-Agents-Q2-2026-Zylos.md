# Claude Agent SDK & Managed Agents: Anthropic's Q2 2026 Agent Infrastructure Play

- URL: https://zylos.ai/research/2026-04-20-claude-agent-sdk-managed-agents-architecture/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-09-01

## 要約
Zylos Research による Claude Agent SDK と Managed Agents の詳細アーキテクチャ分析（2026年4月20日）。Agent SDK: Python/TypeScript ライブラリで自前インフラ上でエージェントループを実行可能、セッション・MCP・サブエージェント対応、既存の Claude プランに課金。Managed Agents（2026年4月8日ローンチ）: Anthropic が実行環境・サンドボックス・セッションログを管理するホスト型 REST API。課金: $0.08/セッション時間＋トークンコスト、2026年6月15日から Pro/Max/Team/Enterprise 対応。推奨パターン: Agent SDK でプロトタイプ → Managed Agents で本番化。自前インフラへのコントロールと Anthropic 管理ランタイムの利便性のトレードオフを詳説。
