# Claude Code Hooks (2026): Block Claude Reading .env + 30 Hook Events, JSON Input, Exit Codes

- URL: https://www.morphllm.com/claude-code-hooks
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-28

## 要約
Claude Code hooksの詳細技術リファレンス。30のhookイベント、5つのハンドラータイプ（command/http/mcp_tool/prompt/agent）、JSONインプット構造（session_id, transcript_path, cwd, hook_event_name, event固有フィールド）を網羅。終了コードセマンティクスの重要な解説：0=成功としてstdout JSONをパース、2=アクションをブロック（対応イベントではstderrをClaudeにフィードバック）、その他=ノンブロッキング。PreToolUseフックで.envファイルへのアクセスをブロックする実装例を特集。パーミッションルールや.gitignoreでは防げない、インデックス経由やsystem-remindインジェクション経由のアクセスも防止できる決定論的な方法として説明。
