# Build Your First AI Agent in Python: Claude Agent SDK Hands-On Guide (August 2026)

- URL: https://medium.com/google-developer-experts/build-your-first-ai-agent-in-python-a-hands-on-guide-to-the-claude-agent-sdk-cb5ba3239dcf
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-29

## 要約
2026年8月公開のClaude Agent SDK Python実践ガイド（Medium/Google Developer Experts）。
- Claude Agent SDKはAnthropicの公式オープンソースPython/TypeScriptライブラリ。Claude Codeと同じエージェントループ・ツール実行エンジン・コンテキスト管理を提供
- エージェントループの仕組み：「計画→ツール呼び出し→結果確認→繰り返し」がチャットボットとエージェントの本質的違い
- インストール方法、SDKのセットアップ、最初のエージェント構築をステップバイステップで解説
- `@tool`デコレータでPython関数をツール化、`client.query()`でエージェントループを起動
- built-inツール（ファイル読み書き・コマンド実行・Web検索/フェッチ）の設定方法
- MCPサーバー、パーミッションモード、フック、サブエージェント、プロバイダルーティングもカバー
- ファイル読み書き・コードベース理解・Web検索の3ツールでリポジトリトリアージエージェントを構築する実例
- 非エンジニアでも90分でエージェントを構築できるよう設計されたガイド
