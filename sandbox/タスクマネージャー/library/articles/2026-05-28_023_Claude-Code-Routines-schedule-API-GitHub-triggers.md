# Claude Code Routines: スケジュール・API・GitHubトリガーによるクラウド自動化

- URL: https://www.infoq.com/news/2026/05/anthropic-routines-claude/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 投稿内容
Anthropic has introduced Routines for Claude Code, allowing developers to configure automated coding workflows that run on schedules, through API calls, or in response to external events. The feature runs on Claude Code's cloud infrastructure, removing the need for developers to maintain their own cron jobs, servers, or automation pipelines locally. A routine consists of a prompt, repository access, and connected tools or services.

## 要約
AnthropicがClaude Code Routinesを発表（2026年4月〜5月）。プロンプト・リポジトリ・コネクターを1パッケージにまとめてClaudeのクラウドインフラで実行するため、ユーザー側にcronジョブ・サーバー・パイプライン不要。3種のトリガー：①スケジュール（バグトリアージ・ドキュメントドリフト検出・PR生成等の定期ジョブ）、②APIトリガー（デプロイパイプライン・監視プラットフォーム・社内ツールがHTTPでClaude Codeセッションを起動）、③GitHubイベント（PR条件に合わせて自動セッション起動、CI失敗追跡・コメント対応・PR全ライフサイクル継続監視）。実際のユースケース：自動イシュートリアージ・デプロイ検証・アラート分析・ドキュメント更新・クロス言語SDK同期。ノーコードツール（Zapier等）の代替として機能する可能性がある新カテゴリ。
