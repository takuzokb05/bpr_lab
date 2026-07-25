# Anthropic API Release Notes 2026: Changes That Reach Claude Code Users

- URL: https://fazm.ai/t/anthropic-latest-api-release-notes-2026
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-07-25

## 投稿内容

fazm.aiによるAnthropic API 2026年リリースノートのまとめ。Claude Codeユーザー視点での変更点解説。

## 要約

- Claude Opus 4.7（4/16）→ Claude Opus 4.8（5/28、APIデフォルト、$5/$25/M tokens、effortパラメータデフォルトがhigh）→ Claude Fable 5（6/9）→ Claude Opus 5（最新デフォルト、1Mコンテキスト、$10/$50/M tokens）という2026年のモデル進化を整理
- Managed AgentsとAnt CLIが4/8に同時リリース
- Python・TypeScript・Go・Java・Ruby・PHP・C# SDKへのコード実行サポート追加（REPLステート永続化）
- 7月のAPIレート制限引き上げ: Claude Sonnet・Haiku がすべての使用ティアで Opus と同等に
- 会話中のツール変更ベータ機能: ターン間でツールを追加/削除しながらプロンプトキャッシュを維持
- Fast mode for Claude Opus 4.7の非推奨（2026/7/24廃止。`speed: "fast"`リクエストはエラーを返す）
- Claude Code wrapperやAPIシステム構築者が把握すべき変更点を網羅した実践的サマリー
