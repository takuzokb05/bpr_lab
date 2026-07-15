# Claude Code Safe Mode & フォールバックチェーン — 本番レジリエンス実践ガイド

- URL: https://www.digitalapplied.com/blog/claude-code-safe-mode-fallback-models-production-resilience-guide
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-06-12

## 要約
Digital Appliedによる2026年6月Claude Code新機能の本番活用ガイド。Safe Mode（--safe-modeまたはCLAUDE_CODE_SAFE_MODE=1）: CLAUDE.md・プラグイン・スキル・フック・MCPを全無効化してクリーンな状態でデバッグするための公式トラブルシュートツール。ユースケース: フックやスキルが競合する問題の切り分け、新しいMCPサーバー追加時の動作確認。フォールバックモデルチェーン（最大3モデル）: プライマリモデルが過負荷（529エラー）または未利用可能な場合に順次試行。設定例: Fable 5→Opus 4.8→Sonnet 4.6の順で設定することで可用性を向上。注意: フォールバック先がプライマリより高コストになるケースに注意。disableBundledSkills設定でビルトインスキル・ワークフロー・スラッシュコマンドを非表示化可能（チームカスタムスキルのみの環境構築に有用）。
