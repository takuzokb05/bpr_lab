# MCP 2026-07-28 仕様リリース候補：ステートレス化・Tasks・認可強化

- URL: https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-06-11

## 要約
Model Context ProtocolのRC版（最終仕様は2026年7月28日公開予定）。最大の変更はプロトコルのステートレス化：初期化ハンドシェイクとセッションIDを廃止し、通常のHTTPラウンドロビンロードバランサーで動作可能になった。従来の粘性セッション管理・共有セッションストアが不要になるため、本番デプロイの複雑さが大幅に減少。主要新機能：MCP Apps（サーバーレンダリングUI）、Tasksエクステンション（長時間実行タスク）、JSON Schema対応ツール定義。認可はOAuth 2.0/OpenID Connectに準拠強化。Breaking changes：エラーコード変更（-32002→-32602）、Roots・Sampling・Loggingを非推奨化。プロダクション利用組織は既存サーバー・クライアントの互換性確認が必要。MCP史上最大の改訂。
