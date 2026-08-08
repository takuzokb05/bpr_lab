# Anthropic Platform Release Notes - August 2026 (Official)

- URL: https://platform.claude.com/docs/en/release-notes/overview
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-08

## 要約
Anthropic公式プラットフォームリリースノート（2026年8月時点）。主要な更新：①code_execution_20260120対応（Python/TS/Go/Java/Ruby/PHP/C# SDK）REPL状態永続化とプログラマティックツール呼び出しをサポート（対応モデル：Claude Fable 5、Mythos 5、Opus 4.5+、Sonnet 4.5+）②MCPトンネル管理APIの移行（/v1/organizations/tunnels → /v1/tunnels、anthropic-beta: mcp-tunnels-2026-06-22ヘッダー必要）③レガシーWorkbenchと実験的プロンプトツールAPIの廃止（2026年8月17日終了）④会話中途のツール変更ベータ（Claude Fable 5、Mythos 5、Opus 4.8、Opus 5対応）プロンプトキャッシュを維持しながらターン間でツールの追加/削除が可能（mid-conversation-tool-changes-2026-07-01ヘッダー必要）。
