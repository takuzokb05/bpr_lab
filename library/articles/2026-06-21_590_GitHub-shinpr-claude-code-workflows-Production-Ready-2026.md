# GitHub: claude-code-workflows — 本番対応のClaude Code専用ワークフロー集（shinpr）

- URL: https://github.com/shinpr/claude-code-workflows
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-21

## 投稿内容
GitHubリポジトリ `shinpr/claude-code-workflows` は、Claude Codeに特化した本番環境対応の開発ワークフロー集。検索クエリ「Claude Code workflow 2026」で上位に表示される実践的リソース。

**主なコンセプト:**
- 専門AIエージェントで動作するプロダクションレディなワークフロー
- SKILL.md形式でClaude Codeのエコシステムとシームレスに統合
- コードレビュー自動化・テスト実行・デプロイパイプラインなど実務ワークフローをカバー

**Claude Codeワークフローの2026年設計原則（本リポジトリを含む複数ソースから）:**
1. **計画先行**: Planモードで実装前にアーキテクチャ確定
2. **並列探索**: subagentsでコンテキスト汚染なく並列調査
3. **永続メモリ**: CLAUDE.md・Memory機能でセッション跨ぎの一貫性
4. **ステップ実行**: 構造化実行でリグレッション防止
5. **セーフガード**: Hooksで破壊的操作をブロック

**2026年のワークフロー進化:**
2025年は「コンテキスト管理」が課題だったが、2026年は「成果物仕様」に重心が移行。CompactionによるコンテキストウィンドウのAI管理、Plan modeによる適切スコープ設定が標準化。

## 要約
GitHubリポジトリ `shinpr/claude-code-workflows`。Claude Code専用の本番対応ワークフロー集。SKILL.md形式でコードレビュー自動化・テスト・デプロイ等をカバー。2026年のClaude Codeワークフロー設計原則（計画先行・並列探索・永続メモリ・構造化実行・Hooks安全機能）を体現したリファレンス実装。
