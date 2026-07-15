# Claude Codeのスキル（Skills）の作り方（2026年6月）

- URL: https://wentz-design.com/post/claude-code-skills-2026-06/
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-08

## 要約
Claude Code Skills（スキル）の作り方を日本語で解説した実践ガイド（2026年6月）。スキルとは：Claudeができることを拡張するMarkdownファイルで、SKILL.mdに指示を書くとClaudeがツールキットに追加する。スラッシュコマンド（/スキル名）またはClaude自身がタスクを検知して自動起動。構造：.claude/skills/スキル名/SKILL.md の1ファイル構成。YAML frontmatter（name + description）とMarkdown本文のみ—descriptionだけ書けば動く最小構成。スキルとMCPとHooksの使い分け：スキルは「繰り返すワークフロー」、MCPは「外部ツール接続」、Hooksは「決定論的自動化」。具体的な作成例（コードレビュー・セキュリティチェック・デプロイ確認等）付き。チームへの展開方法：リポジトリにcommitしてメンバー全員が同じスキルを使う共有が可能。日本語一次資料として価値高。
