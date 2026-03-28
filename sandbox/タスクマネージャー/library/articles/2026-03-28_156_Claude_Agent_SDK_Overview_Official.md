# Claude Agent SDK Overview (Anthropic Official Docs)

- URL: https://platform.claude.com/docs/en/agent-sdk/overview
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-03-28

## 要約

Anthropic公式のClaude Agent SDK（旧称: Claude Code SDK）概要ドキュメント。
- Python・TypeScriptの2言語をサポート
- **カスタムツールの実装方法**: 関数をin-process MCPサーバーとして直接登録可能（別プロセス起動不要）
- `ClaudeSDKClient`クラスによる双方向インタラクティブ会話
- フックとの統合方法（SDK内からhookイベントをトリガーする方法）
- 最新バージョン: Python 0.1.51、TypeScript 0.2.86（npm）

「Claude Code SDK」から「Claude Agent SDK」への名称変更はSDK独立製品としての位置づけを明確にするためで、APIとの統合が強化された。
