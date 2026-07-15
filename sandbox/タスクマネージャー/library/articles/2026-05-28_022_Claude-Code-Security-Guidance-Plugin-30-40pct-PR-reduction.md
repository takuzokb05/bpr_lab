# Claude Code セキュリティガイダンスプラグイン: 25脆弱性クラス3段階検出・PRセキュリティ問題30-40%削減

- URL: https://www.helpnetsecurity.com/2026/05/27/anthropic-claude-code-security-guidance-plugin/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-05-28

## 投稿内容
Anthropic shipped a security-guidance plugin for Claude Code that helps identify and fix vulnerabilities as you're writing code, available for all Claude Code users at no cost. The plugin operates across three distinct review checkpoints: file edits (fast pattern match, no model call), model turns (LLM judgment for logic-level issues), and commits (agentic review reading surrounding callers to minimize false positives). Internal testing showed the plugin cut security-related comments on pull requests by 30–40%.

## 要約
Anthropicが2026年5月27日、Claude Codeセキュリティガイダンスプラグインを全プラン無料で公開。3段階リアルタイム検出：①ファイル編集時（モデル呼び出しなしのパターンマッチ）でeval()/os.system()/child_process.exec()/pickle deserialization/dangerouslySetInnerHTML等の危険コードを即時検出、②モデルターン時（LLM判定）でSQLインジェクション・SSRF・認可バイパス・弱い暗号等ロジックレベルの問題を検出、③コミット時（エージェンティックレビュー）で周辺コード・サニタイザー・呼び出し元を精査し偽陽性を低減。約25種の高リスク脆弱性クラスを検出対象とし、Trail of BitsもGitHubでClaude Code向けセキュリティスキルを公開。内部テストでPRセキュリティコメント30-40%削減を確認。既存のPRコードレビュー機能と連携し多層防御を実現。
