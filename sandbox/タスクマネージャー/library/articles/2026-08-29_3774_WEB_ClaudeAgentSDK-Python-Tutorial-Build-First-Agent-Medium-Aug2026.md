# Build Your First AI Agent in Python: Claude Agent SDK 実践ガイド (Medium, August 2026)

- URL: https://medium.com/google-developer-experts/build-your-first-ai-agent-in-python-a-hands-on-guide-to-the-claude-agent-sdk-cb5ba3239dcf
- ソース: web
- 言語: en
- テーマ: claude-ecosystem
- 取得日: 2026-08-29

## 投稿内容

Medium/Google Developer Expertsに掲載された2026年8月の実践チュートリアル。

**Claude Agent SDKとは:**
- AnthropicのオープンソースPython/TypeScriptライブラリ
- Claude Codeと同一のエージェントループ・ツール実行エンジン・コンテキスト管理を提供
- 違い: ライブラリとして独自Pythonプログラムから呼び出し可能（Claude CLIは不要）

**エージェントとチャットボットの違い:**
- チャットボット: 1問1答
- エージェントループ: 「計画 → ツール呼び出し → 結果確認 → 繰り返し」がタスク完了まで自律実行

**実装ステップ:**
1. `pip install claude-agent-sdk`でインストール
2. `@tool`デコレータでPython関数をツール化
3. `client.query()`でエージェントループを起動

**内蔵ツール:**
- ファイル読み書き・シェルコマンド実行・コードベース理解・Web検索・Webフェッチ

**応用設定:**
- MCPサーバー統合・パーミッションモード設定・フック・サブエージェント・プロバイダルーティング

**実例:**
- リポジトリトリアージエージェント: コードベーススキャン→リスク評価→Markdownレポート生成を90分で構築

## 要約
Claude Agent SDKの入門として最適な実践ガイド。「チャットボットとエージェントの本質的違い」をコードで示しながら、最小限のPythonでAI Agentを構築する手順を丁寧に解説。Claude Codeのスキル・フック・サブエージェントとの設計思想の共通点が理解でき、FX自動取引エージェントへの応用にも直接結びつく内容。`@tool`デコレータパターン・`client.query()`の使い方は日次収集ルーチン・情報収集エージェントの自作に活用可能。
