# Claude Code Security Best Practices: Permissions, Hooks, MCP, Sandboxing, CI/CD

- URL: https://generalanalysis.com/guides/anthropic-claude-code-security-best-practices
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-09-08

## 要約
General AnalysisによるClaude Codeセキュリティベストプラクティス包括ガイド。主要推奨事項：①Default/Plan modeから始め、危険なBashコマンドと機密情報へのdenyルールを設定。②MCP：承認済みサーバーのみ使用、許可ドメインを明示的に制限。③フック（Hooks）：実行前/後に自動検証（pytest、SQL lint等）を走らせてガードレール化。④サンドボックス化：LinuxのPIDネームスペース分離、Dev Container活用。⑤CI/CD統合：OpenTelemetryエクスポートで監査ログ、広範展開前に敵対的検証。⑥CLAUDE.md：ワークフロー誘導に活用するが、エージェントが書き換えられないコントロール（settings.json等）に強制力を持たせる。特筆：CLAUDE.mdに書いたルールはエージェントが意図せず上書きする可能性があり、真のガードレールはsettings.jsonやhooksで実装する必要がある点が重要な指摘。
