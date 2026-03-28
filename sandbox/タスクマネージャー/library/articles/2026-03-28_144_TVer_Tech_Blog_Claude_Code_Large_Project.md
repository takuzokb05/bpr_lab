# 前提知識ゼロでもAIで乗り切った！大規模プロジェクトでのClaude Code活用術 (TVer Tech Blog)

- URL: https://techblog.tver.co.jp/entry/claude-code-use
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-03-28

## 要約

動画配信サービスTVerのエンジニアチームによる、大規模リポジトリでのClaude Code本番活用事例。
- **GitHub Issue起点ワークフロー**: IssueをClaude Codeに渡すだけで、リポジトリ横断探索→実装→PR作成まで自律実行
- 前提知識ゼロ（特定コードベース知識なし）の状態でも70%以上のIssueが自律解決されたという実績
- **クロスリポジトリ探索**: 複数リポジトリにまたがる依存関係をClaude Codeが自動追跡
- 失敗パターン：コンテキストが巨大すぎてハルシネーションが増加→`/compact`定期実行で解決

「AIに投げる前の準備（Issue記述の品質）」がアウトプットに最も影響するという運用知見も含む。
