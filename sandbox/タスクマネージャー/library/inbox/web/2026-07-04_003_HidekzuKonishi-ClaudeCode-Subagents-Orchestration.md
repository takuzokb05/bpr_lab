# Claude Code Subagents and Multi-Agent Orchestration Guide

- URL: https://hidekazu-konishi.com/entry/claude_code_subagents_and_orchestration_guide.html
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-04

## 要約
Claude Code サブエージェントと多エージェントオーケストレーションの完全ガイド。サブエージェントは独立したコンテキストウィンドウを持つ別Claudeインスタンス。親スレッドに結論のみ返し中間作業を隔離する。主要利点：コンテキスト保護・並列化・最小権限の原則。カスタムエージェント定義は `.claude/agents/` にYAML frontmatter付きMarkdownファイルで配置。toolsフィールド省略時は全ツールが付与される（空にはならない）。重要制約：サブエージェントは `AskUserQuestion` 使用不可・バックグラウンドサブエージェントは確認を自動拒否するため承認ゲート付き編集は失敗する。最適ユースケースは大量の読み取り専用調査・独立した並列タスク。密結合な繰り返し作業・人間承認が必要な作業には不向き。
