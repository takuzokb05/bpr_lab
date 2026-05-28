# Claude Code Routines: スケジュール・API・GitHubトリガーでクラウド自動化

- URL: https://www.infoq.com/news/2026/05/anthropic-routines-claude/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 要約
AnthropicがClaude Code Routinesを発表。プロンプト・リポジトリ・コネクターを1パッケージにまとめClaudeのクラウドインフラで実行するため、ユーザー側にcronジョブ・サーバー・自動化パイプライン不要。3種のトリガー：①スケジュール（バグトリアージ・ドキュメントドリフト検出・PR生成等の定期ジョブ）、②APIトリガー（外部システムがHTTPでClaude Codeセッションを起動）、③GitHubイベント（PRの状態変化を監視し自動でCI追跡・コメント対応）。実際のユースケース：自動イシュートリアージ・デプロイ検証・アラート分析・SDK間同期。ノーコードツールの代替として機能。DevOps自動化の新カテゴリを形成する可能性。
