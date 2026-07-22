# Building verification loops in Claude Code with skills — Anthropic Blog

- URL: https://claude.com/blog/building-verification-loops-in-claude-code-with-skills
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-22

## 要約
Anthropic公式ブログ（7月22日）。繰り返しの手動チェックをスキルとして自動化することで、Claudeが自律的にフィードバックループを閉じる方法を解説。スキルは .claude/skills/ 配下の Markdown ファイルで定義。4つのデプロイパターン：スタンドアロン（セキュリティスキャン等）、埋め込み（他スキルに組み込む）、チェーン（シーケンシャル実行）、PR全体（チーム全体に適用）。「Reject any migration that drops a column without a backfill step」のような汎用リンターが捕捉できないビジネスルールをスキルとして実装する具体例を紹介。チームで使うと1人の2分節約が全員の節約になる。
