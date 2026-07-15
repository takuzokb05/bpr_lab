# Claude Code Subagents 2026 実践ガイド — 並列ワークフローで50-70%時間削減

- URL: https://www.tembo.io/blog/claude-code-subagents
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-01

## 要約
tembo.ioによるClaude Code Subagentsの実践ガイド。Subagentは親エージェントがspawnする独立したClaude instanceで、互いに並列実行しながら結果を報告する設計。
Background subagents（Ctrl+B）でメイン会話と完全並列実行。v2.1.117+からFork mode（`CLAUDE_CODE_SUBAGENT_MODEL` 環境変数）でコスト上限・コンプライアンス制御が可能。
2026年中頃の時点で1開発者あたり4〜8並列worktreeが安定稼働、複雑タスクの完了時間を50-70%削減と報告。
YAML定義ファイルで再利用可能なSubagent構成を管理し、Agent Viewダッシュボードで複数セッションを可視化。
orchestrator（リード）がタスクを分割し、specialists（専門家subagent）が並列処理する設計パターンを実例付きで解説。
