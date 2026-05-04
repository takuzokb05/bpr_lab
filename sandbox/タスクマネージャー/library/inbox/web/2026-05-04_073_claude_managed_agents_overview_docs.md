# Claude Managed Agents Overview - Official Docs

- URL: https://platform.claude.com/docs/en/managed-agents/overview
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-05-04

## 要約
Anthropic公式のClaude Managed Agentsドキュメント概要ページ。Managed AgentsはエージェントループとサンドボックスをAnthropicが完全ホストするREST API。開発者のアプリケーションはイベントを送信しSSEで結果をストリーミング受信するだけでよく、インフラ管理が不要。Managed Agentsが提供する機能：安全なサンドボックス環境・組み込みツール（ファイル読み取り・コマンド実行・Web閲覧・コード実行）・スケーリング・可観測性・ログ。Agent SDKとの違い：SDKは自プロセス内でエージェントループを実行（インフラ管理が必要）、Managed Agentsはホスト型（インフラ管理なし）。プロトタイプはSDKで、本番はManaged Agentsへという移行パスを推奨。パブリックベータとして現在利用可能な重要機能。
