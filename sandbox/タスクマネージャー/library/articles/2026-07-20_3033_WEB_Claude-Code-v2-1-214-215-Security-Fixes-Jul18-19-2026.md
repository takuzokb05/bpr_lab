# Claude Code v2.1.214-215：パーミッションバイパス修正・自動スキル実行廃止

- URL: https://releasebot.io/updates/anthropic/claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-20

## 投稿内容
Claude Code Week 30 (July 18-19, 2026) release highlights.

**v2.1.215 (July 19):** Claude no longer runs the /verify and /code-review skills on its own; invoke them with /verify or /code-review when you want them.

**v2.1.214 (July 18):**
- Fixed single-segment dir/** allow rules like Edit(src/**) auto-approving writes to nested dir/ directories anywhere in the tree instead of only <cwd>/dir
- Fixed a permission-check bypass affecting commands run in Windows PowerShell 5.1 sessions
- Fixed Bash permission checks to fail closed on file-descriptor redirect forms that bash parses differently than the permission analyzer
- Fixed Bash permission checks misjudging very long commands — commands over 10,000 characters now always prompt instead of running automatically

**v2.1.211 (July 15):** Added --forward-subagent-text flag and CLAUDE_CODE_FORWARD_SUBAGENT_TEXT environment variable to include subagent text and thinking in stream-json output.

## 要約
Claude Code Week 30（7月18〜19日）のリリース内容。v2.1.215（7/19）：`/verify`・`/code-review`スキルが自動実行されなくなった（明示呼び出しのみ）。v2.1.214（7/18）：重要なセキュリティ修正4件 — (1) `Edit(src/**)` のような単一セグメント許可ルールが任意のネストdirへの書き込みを誤って承認するバグ修正 (2) Windows PowerShell 5.1でのパーミッションチェックバイパス修正 (3) Bashのファイルディスクリプタリダイレクト形式の誤判定修正 (4) 10,000文字超コマンドの誤判定修正（超過時は常にプロンプト）。v2.1.211（7/15）：`--forward-subagent-text`フラグ追加。パーミッション関連の重要バグ修正のため、エンタープライズ・セキュリティを重視する環境では早期アップグレードが推奨される。
