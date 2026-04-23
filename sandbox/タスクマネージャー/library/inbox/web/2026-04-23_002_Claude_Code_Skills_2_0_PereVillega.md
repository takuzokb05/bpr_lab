# What Changed in Claude Code Skills 2.0 — 新機能・破壊的変更・注意点まとめ

- URL: https://perevillega.com/posts/2026-04-01-claude-code-skills-2-what-changed-what-works-what-to-watch-out-for/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-23

## 要約
Claude Code Skills 2.0では大きなアーキテクチャ変更が加わった。Skills 2.0で追加された主な機能：スキルがisolated subagentとして実行でき独自のcontext windowを持てる、shellコマンドでlive dataをスキルプロンプトに動的注入できる「inject」機能、使用ツールの制限・モデル上書き・lifecycle hookへの接続・forked contextでの実行が可能に。またskill-creatorが更新されtest evalsをスキル内で実行しClaudeが出力をスコアリングできるようになった（March 2026更新）。破壊的変更としてはskillsディレクトリ構造が変わりSKILL.mdのfrontmatterに新規フィールドが必須化。既存スキルは段階的移行が必要で、古い書き方は動くが新機能は使えないという「サイレント劣化」に注意が必要。Anthropic公式が「Skills 2.0 Migration Guide」をリリース予定だが本記事時点では未公開。
