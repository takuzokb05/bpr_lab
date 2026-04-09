# Claude Code Hooks Reference: All 12 Events [2026] — Production CI/CD Patterns

- URL: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-09

## 要約
Claude Codeの全12フックイベントを網羅したリファレンス記事（2026年）。PreToolUse・PostToolUse・PreCompact・Stop・Notification・UserPromptSubmit・SessionStart・TaskCreated・TeammateIdle・TaskCompleted・PermissionDeniedの各イベントの用途・引数・戻り値を表形式で整理。本番CI/CDでの活用パターンとして「PreToolUseでgit状態確認→Stopで自動lint実行→PostCompactで圧縮後のコンテキスト検証」のパイプラインを紹介。新追加のPermissionDeniedフック（{retry:true}返却でリトライ可）とdefer権限決定（ヘッドレスセッションのポーズ＆再開）の実装例も掲載。Hooks設計の「べからず集」（共有状態への書き込み競合など）も有用。
