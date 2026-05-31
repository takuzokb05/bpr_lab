# Claude Code Hooks Complete Reference 2026: 27イベント・5ハンドラー型・終了コード体系

- URL: https://thepromptshelf.dev/blog/claude-code-hooks-complete-reference-2026/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-31

## 投稿内容
The Prompt Shelf による Claude Code Hooks の完全リファレンス記事（2026年版）。

## 要約
2026年5月時点で利用可能な27のライフサイクルイベントを網羅したリファレンス。主要イベント：SessionStart・Setup・SessionEnd・UserPromptSubmit・UserPromptExpansion・Stop・PreToolUse・PostToolUse等。5種のハンドラー型：①Command hooks（シェルコマンド直実行）、②Prompt hooks（LLMによるセマンティック評価）、③Agent hooks（ツールアクセスを伴う深い分析）、④Notification hooks（外部通知）、⑤Validation hooks（バリデーション）。終了コードセマンティクス：0=成功、1=警告・ログ、2=ブロック（PreToolUseのみ有効）。PreToolUseはセキュリティゲート・ファイル保護・必須レビュー強制の唯一のブロッキングポイント。本番環境でのHooks設計の一次リファレンスとして必須。
