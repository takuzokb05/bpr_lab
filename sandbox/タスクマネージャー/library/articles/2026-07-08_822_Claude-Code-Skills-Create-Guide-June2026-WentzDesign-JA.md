# Claude Codeのスキル（Skills）の作り方（2026年6月）

- URL: https://wentz-design.com/post/claude-code-skills-2026-06/
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-07-08

## 要約
Claude Code Skills（スキル）の作り方を日本語で解説した実践ガイド（2026年6月版）。スキルとは：Claudeができることを拡張するMarkdownファイル（SKILL.md）—スラッシュコマンドまたは自動起動で使用。構造：`.claude/skills/スキル名/SKILL.md`の1ファイル構成、YAML frontmatter（name + description）+Markdown本文のみ、descriptionだけで最小構成が成立。スキルの自動起動：Claudeがタスクを検知してマッチするスキルを自動ロード（スラッシュコマンド不要）。スキル vs MCP vs Hooks の使い分け：スキル=「繰り返すワークフローの自動化」、MCP=「外部ツール接続」、Hooks=「決定論的強制実行」。具体的な作成例付き（コードレビュー・セキュリティチェック・デプロイ確認等）。チーム展開：リポジトリにcommitして全メンバーが同じスキルを共有可能。CLAUDE.mdとの組み合わせ：CLAUDEは200行以内に制限しスキルを活用して詳細指示をモジュール化。
