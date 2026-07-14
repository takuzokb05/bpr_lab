# Claude Code v2.1.207: Auto Mode Default on Bedrock/Vertex AI/Foundry + Security Fixes

- URL: https://dev.classmethod.jp/en/articles/20260711-cc-updates-v2-1-207/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-14

## 要約
Claude Code v2.1.207（2026年7月11日リリース）の主要変更点をDevelopersIOが解説。最大の変更：Bedrock・Vertex AI・Foundryでauto modeがデフォルト有効化（`CLAUDE_CODE_ENABLE_AUTO_MODE`環境変数不要に）。同環境でのデフォルトモデルがClaude Opus 4.8に変更。デスクトップアプリに内蔵ブラウザ追加。セキュリティ修正として非対話実行でコンセントダイアログをバイパスできた重大バグを修正、プラグインフックで`${user_config.*}`記法を拒否しシェルインジェクション防止。ターミナルフリーズ（長いコードブロック・テーブルのストリーミング時）・AWS SSO認証繰り返し（60秒タイムアウトガード追加）・エージェントクラッシュループを修正。クラウド基盤経由利用の組織への影響大。
