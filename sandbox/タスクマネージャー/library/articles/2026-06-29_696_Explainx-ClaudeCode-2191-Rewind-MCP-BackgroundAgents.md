# Claude Code 2.1.191: /rewind・MCP認証自動再接続・CPU37%削減

- URL: https://www.explainx.ai/blog/claude-code-2-1-191-rewind-mcp-background-agents-2026
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-29

## 要約
Claude Code v2.1.191 changelogの詳解記事。主要アップデート4点：(1)/rewindコマンド追加——/clear実行前の会話状態に戻れる機能。コンテキスト損失を防ぎ、誤ってクリアした場合の復旧が可能に。(2)MCP headersHelper認証改善——401/403エラー返却時にヘルパーが自動再実行して再接続、OAuth再試行ロジックを強化。MCP接続の安定性が大幅向上。(3)Background agentの信頼性向上——バックグラウンドサブエージェントがメインセッションにパーミッションプロンプトを転送するよう変更。バックグラウンド処理が止まる問題の主因解消。(4)ストリーミング中CPU使用率を約37%削減。実用性の高い改善が複数含まれるマイナーリリースだが、MCP運用者・並列エージェント利用者には特に重要。
