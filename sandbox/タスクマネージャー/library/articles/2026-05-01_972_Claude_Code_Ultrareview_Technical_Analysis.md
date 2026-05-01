# /ultrareview in Claude Code: クラウドバグハンターの技術解析（Pasquale Pillitteri）

- URL: https://pasqualepillitteri.it/en/news/1301/claude-code-ultrareview-agents-cloud-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-01

## 要約
`/ultrareview`機能の詳細技術解説。通常の`/review`との差分：フリートエージェントがリモートサンドボックスで動作し再現可能なバグのみ報告する「検証優先アーキテクチャ」。動作フロー：ブランチdiff分析→Logic/Security/Performance等各特化エージェントが並列で異なる角度から検証→再現確認済み発見事項のみをレポート。引数なし実行では現ブランチ↔デフォルトブランチのdiff全体（未コミット・ステージング変更含む）を対象。`/ultrareview --help`でオプション確認。大規模リポジトリはdraft PRを先に作成し`/ultrareview <PR番号>`で実行推奨。CodeRabbit・Greptile等の既存コードレビューAIとの比較（独立再現確認の有無が主差別化点）も掲載。Claude Code v2.1.86以降でのみ利用可能。
