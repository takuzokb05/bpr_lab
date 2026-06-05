# Claude Code Workflow: How It Works and How to Use It in Production

- URL: https://www.truefoundry.com/blog/claude-code-workflow-guide
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-05

## 投稿内容
TrueFountryによるClaude Codeのプロダクション実用ガイド。コンテキストウィンドウ管理（リサーチにサブエージェント活用・新タスクは新セッション開始）、10-15セッション並列実行+gitワークツリーによる衝突防止、claude --resumeによるセッション継続の実践。プランモード活用で複雑タスクの前に仮定を検証。/reviewによる自己レビュープロセス。セッション終了時にClaudeへ学習内容を問い保存する振り返りルーティン。GitHub CLI連携でのPR作成・CI確認のワークフロー詳解。

## 要約
TrueFountryによるClaude Codeプロダクション運用ガイド。実装可能なベストプラクティス群：①サブエージェントでリサーチしコンテキスト節約、②10-15並列セッション+独立gitワークツリーで大規模並列開発、③/reviewによる自己品質改善ループ、④セッション後の振り返りをCLAUDE.md/rules/skillに分類保存。GitHub CLI連携は特に有効。FX自動取引開発を並列化する際のワークフロー設計の参考になる具体的手順書。
