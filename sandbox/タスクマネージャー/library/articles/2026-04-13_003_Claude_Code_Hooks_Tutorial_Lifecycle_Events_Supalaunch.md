# Claude Code Hooks Tutorial: Automate Workflows with Lifecycle Events

- URL: https://supalaunch.com/blog/claude-code-hooks-tutorial-automate-workflows-with-lifecycle-events-guide
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-13

## 要約
Claude Codeのhooksシステムを活用したワークフロー自動化の実践チュートリアル。5つのライフサイクルイベント（PreToolUse/PostToolUse/PostToolUseFailure/PermissionRequest/PermissionDenied）で自動実行されるシェルコマンド/HTTPエンドポイント/LLMプロンプトを解説。設定は.claude/settings.json（プロジェクト共有）または~/.claude/settings.json（個人グローバル）に記述。MCPサーバーのツールもmcp__<server>__<tool>パターンで通常ツールと同様にマッチング可能。CLAUDE.mdが推奨的なのに対しhooksは決定論的で必ず実行される点が差別化要素。Edit|Writeでファイル変更、Bashでコマンド実行を検知する具体的なマッチャー設定例と、CI/lint自動実行・ログ記録・承認通知の実装例を含む。
