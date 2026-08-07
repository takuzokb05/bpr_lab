# Claude Code Multi-Agent Orchestration: 6 Patterns (2026) — The Prompt Shelf

- URL: https://thepromptshelf.dev/blog/claude-code-multi-agent-orchestration-patterns-2026/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-07

## 要約

公式Claude Codeドキュメントを根拠としたマルチエージェントオーケストレーション6パターンのリファレンス（AGENTS.md設定例つき）。

**6パターン**:
1. **Sequential Chain**: タスクAが完了したらBを起動。文書作成→レビュー→公開のような直線フロー
2. **Parallel Fan-Out**: 独立したサブタスクを並列に分配。テストスイートを複数エージェントで同時実行
3. **Hierarchical Delegation**: オーケストレーターが専門エージェントを管理。ルーターとして機能
4. **Consensus / Voting**: 同じ問題を複数エージェントで独立評価し多数決。コードレビューに有効
5. **Peer Review Loop**: エージェントAが成果物を生成し、エージェントBが批評、Aが修正
6. **Recursive Decomposition**: 大タスクをサブタスクに分解し再帰的に処理

**実装Tips**:
- Anthropicの推奨: 多くのワークフローで3〜5サブエージェント
- ファンアウトパターンでは5〜10件のバッチに分ける
- AGENTS.mdのname/description/toolsフロントマターで役割を明示する

**なぜ重要か**: 日次収集ルーチンや情報キュレーションパイプラインへの応用として直接参考になる。特にConsensusパターンはSIGNAL/NOISE分類の精度向上に使える。
