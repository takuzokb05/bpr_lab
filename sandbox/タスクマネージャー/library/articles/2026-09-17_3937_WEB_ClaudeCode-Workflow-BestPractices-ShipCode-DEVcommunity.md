# Claude Code Workflow: Best Practices That Ship Code

- URL: https://dev.to/galian/claude-code-workflow-best-practices-that-ship-code-na
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-17

## 要約
DEV.io掲載のClaude Code実用ワークフロー記事。「実際に出荷できるコード」を書くための習慣論。

**中核ワークフロー（7つの習慣）**:
1. **精簡なCLAUDE.md**: バージョン管理された生きた文書、知識はリポジトリと共に移動。肥大化・陳腐化は何もないより悪い
2. **Plan Mode優先**: Shift+Tab×2でPlan Mode、そこで複数決定を集約（各決定が約100%の確率でランディング）、実装前に仕様をレビュー
3. **ノイジーな調査にはSubagents**: コンテキスト汚染防止
4. **gitワークツリーで並列エージェント**: 複数ブランチを独立して並列実行
5. **Hooksをガードレールとして**: lint・安全チェック・副作用の自動化
6. **繰り返しタスクはSkillに**: 週1回以上のタスク、一貫した出力要件があるもの（コードレビュー・コンテンツフォーマット・リサーチ統合等）
7. **検証ループ**: 幻覚を殺すための反復確認

**「インフラとして使う人 vs チャットボットとして使う人」格差**:
- 自動ロードされるファイル・必要時に発火するSkills・眠っている間に動くワークフローを構築する人が加速
- 毎回プロンプトを書く人との差が月を追うごとに拡大
- "The people pulling ahead are building systems"（先行する人はシステムを構築している）

**拡張プリミティブの使い分け要約**:
- 強制すべきルール → Hooks/権限
- contextual知識 → Skills
- 委譲境界 → Subagents
- 常時稼働プロジェクト指針 → CLAUDE.md（短く）
