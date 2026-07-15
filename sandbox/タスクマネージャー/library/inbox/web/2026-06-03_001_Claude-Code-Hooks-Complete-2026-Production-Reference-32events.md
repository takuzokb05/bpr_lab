# Claude Code Hooks: The Complete 2026 Production Reference (32+ Events, 5 Handler Types)

- URL: https://thepromptshelf.dev/blog/claude-code-hooks-complete-reference-2026/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-03

## 要約
Claude Code Hooksの2026年完全リファレンス。v2.1.141+時点で27の独立したイベントが存在（SessionStart, Setup, SessionEnd, UserPromptSubmit, UserPromptExpansion, Stop, StopFailure, PreToolUse, PostToolUse, PostToolUseFailure, PostToolBatch, PermissionRequest, PermissionDenied, SubagentStart, SubagentStop, TeammateIdle, TaskCreated, TaskCompleted, InstructionsLoaded, ConfigChange, CwdChanged, FileChanged, WorktreeCreate, WorktreeRemove, PreCompact, PostCompact, Notification, Elicitation, ElicitationResult）。ハンドラータイプは5種類：http（URLにPOST）、mcp_tool（接続済みMCPサーバーのツール呼び出し）、prompt（シングルターンLLM評価）、agent（マルチターン検証）、shell（シェルコマンド）。PreToolUseはexit 2でブロック可能、PostToolUseはobservability専用（元に戻せない）。実設定はsettings.jsonのhooksキーに記述。P-018「Hooks27イベント文書化」の一次情報として価値高。
