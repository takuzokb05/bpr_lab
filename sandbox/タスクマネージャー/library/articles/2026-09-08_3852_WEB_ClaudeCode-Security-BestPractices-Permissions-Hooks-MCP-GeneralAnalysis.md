# Claude Code セキュリティベストプラクティス — パーミッション・Hooks・MCP・サンドボックス・CI/CD

- URL: https://generalanalysis.com/guides/anthropic-claude-code-security-best-practices
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-08

## 投稿内容
General AnalysisによるClaude Codeセキュリティベストプラクティス包括ガイド。

## 要約
Claude Codeのセキュリティ姿勢確立のための実践的推奨事項：①Default/Plan modeから始め、危険なBashコマンドと機密情報へのdenyルールを設定。②MCP：承認済みサーバーのみ使用、allowed_domains/blocked_domainsで許可ドメインを明示制限（Anthropicが9月にweb_search/web_fetchツールへのドメイン制限機能追加済み）。③Hooks：実行前/後に自動検証（pytest・SQLlint等）を走らせてガードレール化。④サンドボックス化：LinuxのPIDネームスペース分離、Dev Container活用。⑤CI/CD統合：OpenTelemetryエクスポートで監査ログ、広範展開前に敵対的検証。⑥CLAUDE.md：ワークフロー誘導には有効だが、エージェントが書き換えられないsettings.json・hooksに真の強制力を持たせること。重要知見：CLAUDE.mdに書いたルールはエージェントが意図せず上書きする可能性があり、真のガードレールはsettings.jsonやhooksで実装する必要がある。
