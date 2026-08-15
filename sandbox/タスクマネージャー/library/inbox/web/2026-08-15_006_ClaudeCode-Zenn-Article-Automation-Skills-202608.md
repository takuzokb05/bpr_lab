# Zenn投稿をClaude Code Skillsで自動化してみた

- URL: https://zenn.dev/katsuo_dev/articles/202608-claude-code-zenn-automation
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-08-15

## 要約
Zenn 記事。Claude Code Skillsを使ってZenn記事投稿ワークフローを自動化した実践報告。SKILL.md にZenn記事のフォーマット・投稿手順・frontmatter規則を定義し、スラッシュコマンド1本で「下書き→frontmatter生成→zenn-cli publish」までを自動化。2026年8月時点では npm 経由インストールは非推奨でネイティブインストーラー推奨。/model コマンドでタスクの重さに応じてOpus/Sonnet/Haikuを使い分けることでコスト最適化も実現。個人ブログ執筆への Claude Code 応用事例として参考になる。
