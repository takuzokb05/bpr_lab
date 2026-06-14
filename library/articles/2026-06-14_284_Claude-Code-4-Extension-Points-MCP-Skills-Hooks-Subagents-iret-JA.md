# Claude Code本気カスタマイズ: MCP・Skills・Hooks・Subagentsの4拡張点完全解説

- URL: https://iret.media/198214
- ソース: web
- 言語: ja
- テーマ: claude-code
- 取得日: 2026-06-14

## 投稿内容
Claude Codeを本気でカスタマイズしてみた：【第1回】4つの拡張点 | iret.media（クラスメソッドグループ）

MCP: 外部ツール・APIへの接続（ブラウザ自動化、DB操作、外部サービス連携）
Skills: 繰り返しワークフローのtemplate化（.mdファイルで定義するスラッシュコマンド）
Hooks: 32種類のライフサイクルイベントへの自動応答（PreToolUse, PostToolUse等）
Subagents: 並列タスク処理（@mention構文でサブエージェント起動）

実践事例: AWSインフラ構築プロジェクトでの4拡張点組み合わせ。コミット前自動テスト（Hooks）＋インフラテンプレート生成（Skills）＋AWS MCP Server（MCP）＋並列リソース作成（Subagents）の組み合わせ。

## 要約
iret.media（クラスメソッドグループ）によるClaude Code 4拡張点の実践的日本語解説。MCP・Skills・Hooks・Subagentsそれぞれの役割・使い分け・実装方法を図解で解説。MCPは外部ツール・API接続（browseruse、DBツール、AWS等）、Skillsは繰り返しワークフローのテンプレート化（.mdファイルで定義）、Hooksは32種類のライフサイクルイベントへの自動応答（コミット前テスト等）、Subagentsは並列タスク処理。AWSインフラ構築での組み合わせ事例を詳細解説。JA圏では数少ない4拡張点を体系的かつ実践的に比較した技術記事。特にHooks（PreToolUse/PostToolUseを使ったCI/CD連携）の具体実装例が詳しく、本格運用を検討しているチームに有用。
