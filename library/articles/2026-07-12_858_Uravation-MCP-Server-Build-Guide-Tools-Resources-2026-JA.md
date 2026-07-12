# MCP Server構築完全ガイド2026｜Tools/Resources/Prompts実装パターン

- URL: https://uravation.com/media/anthropic-mcp-server-build-tools-resources-prompts-2026/
- ソース: web
- 言語: ja
- テーマ: claude-ecosystem
- 取得日: 2026-07-12

## 要約
UravationによるMCPサーバー構築の完全ガイド（2026年版）。3コア機能の実装パターンをコード付きで解説。

**MCPの3コア機能**:
- **Tools**: AIが呼び出せる関数（外部API・DBクエリ・計算等）
- **Resources**: AIが読めるデータ源（ファイル・API応答・DB記録）
- **Prompts**: 定義済みテンプレート（特定タスク向けプリセット）

**2トランスポートの選択基準**:
- STDIO: ローカル実行向け・レイテンシ約1ms・子プロセス型
- Streamable HTTP: リモートデプロイ向け・レイテンシ10-100ms・水平スケーリング対応

**本番セキュリティ設計**:
- 最小権限原則の徹底（不要なツールを公開しない）
- 入力サニタイズ（インジェクション対策）
- 認証パターン（OAuth 2.0 / APIキー）の実装例付き

**エコシステム状況**:
- 2026年4月時点でmcp.soに約19,700件のサーバー登録済み
- 国産SaaS（freee・kintone・Sansan等）との連携対応が本格化

FastMCP 3.0（デコレータ1行でPythonサーバー実装）を使った実装例も提示。P-011（カスタムMCPサーバー開発）の具体的な実装参考資料として活用可能。
