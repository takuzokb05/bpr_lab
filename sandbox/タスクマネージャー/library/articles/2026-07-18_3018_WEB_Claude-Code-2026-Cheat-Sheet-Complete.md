# Claude Code 2026完全チートシート：コマンド・MCP・Hooks・スキル使い分け

- URL: https://techbytes.app/posts/claude-code-2026-cheat-sheet-hooks-mcp-commands/
- ソース: web
- 言語: en
- テーマ: claude-code
- 取得日: 2026-07-18

## 投稿内容
TechBytesによるClaude Code 2026年版完全チートシート（スラッシュコマンド・MCP・Hooks・ショートカット網羅）。4種のHook：(1) HTTPフック（JSON POST送信）、(2) MCPツールフック（接続済みMCPサーバーのツール呼び出し）、(3) プロンプトフック（Claude単一ターン評価）、(4) エージェントフック（ツール使えるサブエージェント起動）。使い分け原則：スラッシュコマンド=プロンプトテンプレート、スキル=ドメインロジック＋ヘルパーファイル、フック=コードでルール強制。最小構成推奨：短CLAUDE.md・スコープ済み.mcp.json・安全フック・再利用スキル各1個。Week 29新機能もカバー：/voice（スペースバーpush-to-talk）・/cd（ディレクトリ変更・キャッシュ維持）・--safe-mode（全カスタマイズ無効化）。CLAUDE.md：200行以下推奨、HTML commentはトークン消費なし。

## 要約
Claude Code 2026年の設定・拡張を一枚でまとめたリファレンス。Hook 4種の使い分けが整理されており実装判断に役立つ。最小構成の考え方は過剰設定防止に有用。タスクマネージャーのスキル設計・CLAUDE.md最適化の参考として即活用できる。
