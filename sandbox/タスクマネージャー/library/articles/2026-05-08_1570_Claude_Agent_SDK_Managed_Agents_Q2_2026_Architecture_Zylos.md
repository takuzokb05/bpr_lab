# Claude Agent SDK & Managed Agents: Anthropic's Q2 2026 Agent Infrastructure Play

- URL: https://zylos.ai/research/2026-04-20-claude-agent-sdk-managed-agents-architecture
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-08

## 投稿内容

Zylos Research による Claude Agent SDK と Managed Agents の詳細アーキテクチャ分析（2026年Q2）。

## 要約

Anthropic は Q1-Q2 2026 に2製品を展開：Claude Agent SDK（自己ホスト型・コードベース統合）と Managed Agents（ホスト型インフラAPI、2026年4月8日パブリックベータ開始）。両者の違い：Agent SDK はコードに統合してローカル制御・プログラマティックなエージェント定義、Managed Agents は API エンドポイント経由でクラウド実行・インフラ管理不要。Managed Agents の技術仕様：secure sandboxing、built-in tools、server-sent event streaming、セッション管理API、全エンドポイントに managed-agents-2026-04-01 ベータヘッダーが必要。Anthropic のエンジニアリングブログで公開の推奨アーキテクチャ：Planner agent → Generator agent → Evaluator agent の3層構成が長時間エージェント向けの production-validated パターン。Agent SDK は tool-use-first アプローチで、他エージェントをツールとして呼び出す MCP 最深統合が最大の強み。
