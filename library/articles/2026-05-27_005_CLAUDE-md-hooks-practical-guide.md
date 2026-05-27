# CLAUDE.mdとHooksの実践ガイド: 助言的指示と決定論的自動化の使い分け

- URL: https://medium.com/becoming-for-better/taming-claude-code-a-guide-to-claude-md-and-hooks-ed059879991c
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-27

## 投稿内容
Medium「Becoming for Better」に掲載のCLAUDE.md・Hooks実践ガイド。

## 要約
CLAUDE.mdは「助言的」（Claudeが無視できる）、Hooksは「決定論的」（必ず実行される）という本質的な違いを明確化。CLAUDE.mdの書き方：新入りエンジニアへのオンボーディング指示書スタイル（簡潔・直接的・行動指向、500語以内推奨）。含めるべき内容：テックスタック、エントリーポイント場所、命名規則、build/test/lint用コマンド、共通の落とし穴、チームのコーディングスタイル。Hooksの実践例：危険コマンドのブロック（rm -rfなど）、編集後のフォーマッタ自動実行、PreCompact/PostCompactのログ記録。「絶対に例外なく実行されるべき」自動化はHooks、「Claudeへの推奨/指針」はCLAUDE.mdという明快な分類ルールが有用。
