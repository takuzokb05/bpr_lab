# Claude Code Hooks: A Practical Guide to Workflow Automation (DataCamp)

- URL: https://www.datacamp.com/tutorial/claude-code-hooks
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

DataCampによるClaude Codeフックの実践ガイド。各ライフサイクルイベントで渡されるJSONデータ構造を詳細解説：
- **21種類のフックイベント**（PreToolUse, PostToolUse, PreCompact, SessionStart等）のユースケース一覧
- `stdin`から受け取るJSONの正確なスキーマ（tool_name, input, output フィールド等）
- exit codeセマンティクス（0=許可、2=ブロック、その他=非ブロッキング警告）の具体例
- `settings.json` でのフック登録方法とmatcherパターン（glob対応）

フックスクリプトへの入力データを正確に把握するための参照ドキュメントとして有用。
