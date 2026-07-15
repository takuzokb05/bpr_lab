# Medium: Agent Teams with Claude Code and Claude Agent SDK —実装ガイド

- URL: https://kargarisaac.medium.com/agent-teams-with-claude-code-and-claude-agent-sdk-e7de4e0cb03e
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-27

## 要約
Isaac KargarによるMedium記事（2026年2月11日）が、Claude Codeの「**Agent Teams**」機能を理論・実装の両面で詳解。Agent Teamsは並列処理・異なる視点による検証が必要な場面で有効。有効化方法：環境変数 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` を設定。主要ツール：`TeamCreate`（チーム作成）、`SendMessage`（エージェント間メッセージ）、`TeamDelete`（チーム削除）。実装パターンとして `ClaudeAgentOptions` クラスでenv設定を指定する方法を解説。実例デモ：4エージェント構成（アーキテクト・実装者・テスター・ドキュメント作成者）でタスクランナーCLIを協調構築し、テスターが発見した障害をリアルタイム修正するエージェント間通信フローを実演。Claude Code内での専用チームとClaude Agent SDKでの外部チームの2種類のアーキテクチャパターンを比較。Dynamicワークフロー機能の基礎として位置付けられる実践的な技術記事。
