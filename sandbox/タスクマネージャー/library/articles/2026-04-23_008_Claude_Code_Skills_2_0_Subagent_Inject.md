# Claude Code Skills 2.0 の変更点まとめ — subagent実行・動的注入・テストevalが核心

- URL: https://perevillega.com/posts/2026-04-01-claude-code-skills-2-what-changed-what-works-what-to-watch-out-for/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-04-23

## 要約
Claude Code Skills 2.0の技術的変更を詳述した実践レポート。主な新機能：①スキルがisolated subagentとして実行可能になり独自のcontext windowを持てる（メイン会話からの汚染を防止）、②「inject」機能でshellコマンドをスキルプロンプトに動的注入しリアルタイムデータを渡せる、③使用ツールを制限・モデルを上書き・lifecycle hookに接続・forked contextで実行可能、④skill-creatorにtest evals機能追加（Claudeがスキル出力をスコアリング）。破壊的変更としてSKILL.mdフロントマターの必須フィールドが変更。既存スキルは旧書き方でも動くが新機能が使えない「サイレント劣化」に注意。Claude Code Skills 2.0 Migration Guideは記事執筆時点で未公開。CLAUDE.mdやスキル設計を見直す際の重要参考情報。
