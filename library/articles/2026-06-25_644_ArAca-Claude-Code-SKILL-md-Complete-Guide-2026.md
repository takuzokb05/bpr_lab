# Claude Code SKILL.mdの書き方と活用方法徹底解説【2026年版】

- URL: https://ar-aca.tech/posts/claude-code-skills-guide/
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-25

## 要約
ar-aca.tech（Arcadia Academia）によるClaude Code Skills（SKILL.md）の完全ガイド記事。
スキルの2タイプを詳解：
- **常時ロード型**：プロジェクトコンテキストに基づいてClaudeが自動的にロード。`description`フィールドをClaudeが読んでロード判断
- **明示起動型**（`disable-model-invocation: true`）：ユーザーが`/name`で明示的に起動。コミットやPR作成など副作用を伴うワークフローに推奨
実践的な記述ガイド：
- `name`・`description`・`steps`の最低限フィールド構成
- WHY/WHAT/HOW三段構造での手順記述
- スキルとCLAUDE.md・Hooksの使い分け基準（CLAUDE.md→ガイダンス80%適用、Hooks→確定100%実行、Skills→専門知識のカプセル化）
bpr_labのスキルシステム設計や既存スキルの改善に直接参考になる一次情報。
