# Claude Code /ultrareview: the Bug-Hunting Agent Fleet in the Cloud (April 2026)

- URL: https://pasqualepillitteri.it/en/news/1301/claude-code-ultrareview-agents-cloud-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-01

## 要約
`/ultrareview`機能の技術解説記事。単純な構文チェックや静的パターンマッチングを超え、クラウドサンドボックス上の専門バグハンターエージェント群が深層ロジック欠陥とセキュリティ脆弱性を発見する。動作仕組み：ブランチのdiffを分析→複数エージェントが「ロジック」「セキュリティ」「パフォーマンス」等それぞれ異なる角度で検証→再現可能性確認済み発見事項のみレポート。引数なし実行では現ブランチとデフォルトブランチのdiff全体（未コミット・ステージング済み変更含む）を対象。大規模リポジトリはdraft PRを先に開いて`/ultrareview <PR番号>`で実行推奨。`/ultrareview --help`でオプション確認。Claude Opus 4.7と同時リリースされた背景と、コードレビュー市場（CodeRabbit・Greptile等）との差別化ポイントも解説。
