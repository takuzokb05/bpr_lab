# LLM 0.32リリース: リーズニングトレース・OpenAI Responses API・サーバーサイドツール対応

- URL: https://simonwillison.net/2026/Aug/4/new-release-of-llm/
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-08-05

## 投稿内容
Simon WillisonによるLLM 0.32公式リリース発表（2026年8月4日）。初期リリース以来最重要アップデートと位置づけ。主要4機能と新デフォルトモデルGPT-5.6 Lunaを紹介。

## 要約
Simon Willison（Django共同創設者・AI開発者）によるオープンソースLLMツール「LLM」バージョン0.32のリリース発表（2026年8月4日）。LLM初期ローンチ以来最も重要なリリースと位置づける。主要新機能4つ：①可視化されたリーズニングトレース（Claude Sonnet/Opus、o3等の内部思考プロセスをCLIで表示可能）、②OpenAI Responses APIサポート（GPT-5.6ファミリーとサーバーサイドツールに対応するための新API形式）、③サーバーサイドプロバイダーツール（Web検索・コード実行をプロバイダー側で処理してクライアント複雑性を削減）、④再設計されたコンテンツアドレス可能SQLiteログ（セッション跨ぎでの検索・照合が大幅改善）。デフォルトモデル変更：GPT-5.6 Luna（$0.20/$1.20/Mトークン）に。`pip install -U llm`でアップグレード。LLMはClaude・GPT・Gemini・Mistral等多数のプロバイダーをCLIから統一インターフェースで利用できるツールで、AI開発者・研究者に広く使われている。
