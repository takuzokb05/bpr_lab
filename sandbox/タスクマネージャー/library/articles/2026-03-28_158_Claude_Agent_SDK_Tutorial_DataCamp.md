# Claude Agent SDK Tutorial (DataCamp)

- URL: https://www.datacamp.com/tutorial/how-to-use-claude-agent-sdk
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-03-28

## 要約

DataCampによるClaude Agent SDKハンズオンチュートリアル（Claude Sonnet 4.5使用）。
- **セッション再開** (`ClaudeAgentOptions(resume=sdk_session_id)`) による長時間タスクの中断・再開
- ファイル操作・コード実行を含む実践的なエージェント実装例
- **リモートワークスペースパターン**: ローカルPCなしでS3バケットを作業ディレクトリとして使う構成
- エラーハンドリングとリトライロジックのベストプラクティス

セッション再開機能は長時間タスク（1時間以上のバッチ処理等）の実装に不可欠で、本番運用に直結する技術情報。
