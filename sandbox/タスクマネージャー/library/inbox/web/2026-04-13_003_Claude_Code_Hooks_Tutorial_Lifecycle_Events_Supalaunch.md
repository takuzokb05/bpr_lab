# Claude Code Hooks Tutorial: Automate Workflows with Lifecycle Events

- URL: https://supalaunch.com/blog/claude-code-hooks-tutorial-automate-workflows-with-lifecycle-events-guide
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-13

## 要約
Claude Codeのhooksシステムを活用したワークフロー自動化の実践チュートリアル。Hooksはライフサイクルの特定ポイント（PreToolUse/PostToolUse/PostToolUseFailure/PermissionRequest/PermissionDenied）で自動実行されるシェルコマンド/HTTPエンドポイント/LLMプロンプト。設定は.claude/settings.json（プロジェクト共有）または~/.claude/settings.json（個人グローバル）に記述。MCPサーバーのツールも通常ツールと同様にmcp__<server>__<tool>パターンでマッチング可能。CLAUDE.mdの指示が推奨的であるのに対し、hooksは決定論的で必ず実行される点が差別化要素。Edit|Writeでファイル変更、Bashでコマンド実行を検知する具体的なマッチャー設定例を含む。
