# Claude Code /ultrareview: Cloud Bug-Hunting Agent Fleet (April 2026)

- URL: https://pasqualepillitteri.it/en/news/1301/claude-code-ultrareview-agents-cloud-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-02

## 要約
Claude Codeの`/ultrareview`コマンドの詳細解説（April 2026パブリックリサーチプレビュー）。
複数のレビュアーエージェントがPR変更を並列探索し、全ての報告バグを独立再現・検証するクラウドベースのマルチエージェントコードレビューシステム。
標準では5エージェント、大規模変更では最大20エージェントが並列稼働。各エージェントが異なる観点（競合状態、SQLインジェクション、エラーハンドリング等）に特化。
`/review`コマンドとの違い：/ultrareviewはクラウド実行・多段階検証・バグ再現確認まで行い、スタイル提案ではなく実際のバグのみを報告する。
2026年4月のパブリックリサーチプレビュー以降、ProプランでアクセスAPI経由で利用可能。大規模PRや重要なリリース前レビューで特に有用。
