# 効果的なCLAUDE.mdの書き方: 段階的開示・命令予算200個の制約

- URL: https://zenn.dev/farstep/articles/how-to-write-a-great-claude-md
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-05-30

## 要約
Zennの実践記事。CLAUDE.mdはClaude Codeが自動読み込みする設定ファイルで、コンテキストウィンドウの有限性から「1ファイル約200行以内」が推奨されている。重要な制約：LLMが一貫して従える命令数の上限はフロンティアモデルで約200個程度で、命令数増加と共に全命令の遵守率が一律低下する。段階的開示（Progressive Disclosure）の3層構造を提案：Layer 1（CLAUDE.md）必須情報のみ、Layer 2（.claude/rules/）トピック別指示、Layer 3（スキル・エージェント）専門知識。推奨5セクション：プロジェクト概要・コードスタイル・コマンド・アーキテクチャ・注意事項。判断基準：「削除したらClaudeが間違えるか？」でYESなら残す、NOなら削除。コードから自動推論できる情報やリンターで処理できるスタイルルールは書かない。CLAUDE.mdとHooksとSkillsの役割分担（助言/決定論的/再利用可能）を明確化。
