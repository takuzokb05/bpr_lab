# Claude Code 2026年6月大型アップデート — Safe Mode・5段階サブエージェント・レート2倍

- URL: https://jangwook.net/en/blog/en/claude-code-june-2026-new-features-changelog-developer-guide/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-12

## 要約
2026年6月のClaude Code主要アップデートを網羅した開発者ガイド（jangwook.net）。v2.1.168〜v2.1.172の範囲。主要変更点: (1) Safe Mode（--safe-modeフラグ・CLAUDE_CODE_SAFE_MODE環境変数）— CLAUDE.md/プラグイン/スキル/フック/MCP全無効でトラブルシュート可能、(2) /cdコマンド — プロンプトキャッシュ保持しつつ作業ディレクトリ変更、(3) フォールバックモデルチェーン（最大3モデル、6/6-8実装）— 529エラー対策に有効、(4) Claude Fable 5統合（v2.1.170、6/9）、(5) 5段階ネストサブエージェント（v2.1.172、6/10）— サブエージェントが自身のサブエージェントを生成可能、最大5段階のハードキャップ、(6) Pro/Max/Team/Enterprise向けレート制限2倍化、(7) disableBundledSkills設定追加。注目: 5段階ネストは実質「再帰+スタック5フレーム制限」の構造。実用推奨深さは2〜3段階。
