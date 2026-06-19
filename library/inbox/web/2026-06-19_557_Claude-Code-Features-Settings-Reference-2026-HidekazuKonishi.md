# Claude Code Features and Settings Reference 2026

- URL: https://hidekazu-konishi.com/entry/claude_code_features_settings_reference_2026.html
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-19

## 要約
Claude Code の全機能・設定項目を体系的に整理したリファレンス記事（2026年版）。5層アーキテクチャ（CLAUDE.md／MCP／Skills／Hooks／Subagents）の役割分担を図解し、各レイヤーの設定ファイルの場所・書き方・優先順位を網羅する。特に Hooks の PreToolUse・PostToolUse・UserPromptSubmit イベントの使い分けと、Skills の YAML フロントマター設計パターン（auto-trigger vs 手動呼び出し）を詳述。設定ファイルのスコープ（グローバル vs プロジェクト vs セッション）の違いも整理されており、新規セットアップ時のチェックリストとして活用できる。Claude Code v2.1.101以降の変更点を反映済み。
