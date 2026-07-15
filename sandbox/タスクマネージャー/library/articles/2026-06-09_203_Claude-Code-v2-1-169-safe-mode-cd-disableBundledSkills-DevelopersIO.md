# Claude Code v2.1.169 Major Updates — safe-mode, /cd, disableBundledSkills

- URL: https://dev.classmethod.jp/en/articles/20260609-cc-updates-v2-1-169/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-09

## 投稿内容
DevelopersIO（クラスメソッド）によるClaude Code v2.1.169（2026年6月8日リリース）の詳細解説。30変更（新機能3/改善12/修正12/セキュリティ2/パフォーマンス1）を網羅。

新機能3件：
1. `--safe-mode`フラグ（`CLAUDE_CODE_SAFE_MODE`環境変数も可）：CLAUDE.md・プラグイン・スキル・フック・MCPサーバーを全て無効化したクリーンな状態で起動。バグ原因の切り分けに使用。
2. `/cd`コマンド：セッション中にワーキングディレクトリを変更可能、プロンプトキャッシュを壊さずに対応。
3. `disableBundledSkills`設定（`CLAUDE_CODE_DISABLE_BUNDLED_SKILLS`）：バンドルスキル・ワークフロー・組み込みスラッシュコマンドをモデルから非表示にする。

セキュリティ修正2件：(1)未承認プロジェクト設定からのOTELクライアント証明書パス設定を防止、(2)MCP企業管理ポリシー（allowedMcpServers/deniedMcpServers）が特定コードパスで未適用だったバグを修正。

主要改善：Windows版claude -pのスキャン待ちによる遅延・ハングを解消、フォールバックモデルの動作改善（primary model Not FoundでセッションをフォールバックモデルへSwitchするよう変更）。

## 要約
v2.1.169は安全性・利便性・企業管理を大幅強化。--safe-modeは拡張のデバッグに必須ツール、/cdはマルチリポジトリ作業での利便性向上、disableBundledSkillsはクリーンな動作環境確保に有用。セキュリティバグ修正2件（OTEL証明書・MCPポリシー）も本番環境では重要。
