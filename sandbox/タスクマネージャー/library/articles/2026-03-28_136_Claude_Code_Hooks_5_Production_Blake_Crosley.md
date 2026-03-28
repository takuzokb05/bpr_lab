# Claude Code Hooks Tutorial: 5 Production Hooks From Scratch (Blake Crosley)

- URL: https://blakecrosley.com/blog/claude-code-hooks-tutorial
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

本番環境で実際に動作する5つのフックをゼロから構築するチュートリアル。各フックは完全なスクリプトと解説付き：
1. **オートフォーマッター**: PostToolUseでblack/prettier自動実行
2. **セキュリティゲート**: PreToolUseで`.env`・秘密鍵ファイルのコミットをブロック（exit code 2必須）
3. **テストランナー**: 変更ファイルに対応するテストを自動実行
4. **Slack通知**: 長時間タスク完了時に通知送信
5. **プリコミット品質チェック**: lint + type check を自動実行

重要な技術的知見：ブロッキングフックには `exit 1` ではなく **`exit 2`** が必要。`exit 1` は非ブロッキングの警告扱いになる。
