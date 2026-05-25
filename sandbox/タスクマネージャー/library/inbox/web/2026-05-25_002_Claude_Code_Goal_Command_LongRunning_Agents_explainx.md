# Claude Code /goal Command: Set Completion Conditions for Long-Running Agents

- URL: https://explainx.ai/blog/claude-code-goal-command-long-running-agents-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-25

## 要約
explainx.aiによるClause Code `/goal`コマンドの詳細解説記事。`/goal <condition>`を入力するとClaudeが指定条件を満たすまで複数ターンにわたって自律的に作業を継続する。各ターン後にHaikuモデルが条件達成を評価し、未達の場合は自動で次ターン開始。`/goal all tests pass and PR is open`のような自然言語条件を受け付ける。スタック時には人間に報告して停止する安全設計。従来の手動リトライ・監視が不要になり、CI修正・テストグリーン化・PR作成などの反復タスクを完全自動化できる。Agent ViewとのUI統合で全セッションの進捗を一括管理可能。
