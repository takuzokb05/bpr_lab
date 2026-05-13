# Claude Managed Agents「Dreaming」機能解説——エージェントの非同期バックグラウンド処理

- URL: https://www.buildfastwithai.com/blogs/claude-managed-agents-dreaming-explained
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-13

## 要約
Anthropicが公開ベータで提供するClaude Managed Agents（managed-agents-2026-04-01ベータヘッダー必須）の「Dreaming」機能を解説。エージェントがバックグラウンドで自律タスクを実行中の状態を指し、セキュアサンドボックス・組込ツール・SSEストリーミングで動作する。APIはplatform.claude.comのManaged AgentsエンドポイントでMessages APIと同様の構造。Routinesと組み合わせると「スケジュール起動→バックグラウンド実行→結果通知」の完全自動化パイプラインが構築可能。Claude Platform on AWS（IAM認証対応）でも利用可能。
