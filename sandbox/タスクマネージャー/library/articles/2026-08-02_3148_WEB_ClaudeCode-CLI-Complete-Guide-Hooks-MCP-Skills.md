# Claude Code CLI 完全ガイド 2026 — Hooks 17イベント・MCP統合・Skills設計パターン

- URL: https://blakecrosley.com/guides/claude-code
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-08-02

## 投稿内容
Blake CrosleyによるClaude Code CLIの包括的リファレンスガイド（2026年7月更新）。MCP・Hooks・Skillsの3レイヤーを統合的に解説し、最小構成からプロダクション運用まで段階的に構築する方法を提示。

## 要約
Blake Crosleyが2026年7月に更新したClaude Code CLIの包括リファレンス。構成: MCPサーバーで外部ツール（Web検索・スクレイピング・DB）と接続する方法、Hooks全17イベント・4タイプの詳細・3本の本番用サンプルフック、Skillsのフォルダ構造とオンデマンドロードの仕組み。Hooks分類: PreToolUse（ツール実行前ガード）・PostToolUse（結果確認）・Notification（イベント通知）・Stop（セッション終了処理）の4タイプ。実装済みサンプル: gitコミット前のテスト強制実行、rm -rfブロックフック、セッション開始時の環境チェック。Skillsパターン: .claude/skills/[name]/SKILL.md にfrontmatterとマークダウン指示を置くだけでオンデマンドロード可能、プロジェクト特化ドメイン知識をカプセル化。最小構成推奨: CLAUDE.md 1枚・必要なMCPのみの.mcp.json・安全フック1本・再利用スキル1本・サブエージェントは必要時のみ。2026年7月時点の42種組み込みツール（File/Code系 Read/Write/Edit/Glob/Grep/LSP、Shell/Process系 Bash/PowerShell/Monitor）の完全リスト付き。
