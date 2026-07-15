# Open-Source LLM Trading Bot with Full Backtesting 公開 (GoPenAI)

- URL: https://blog.gopenai.com/i-just-released-an-open-source-llm-trading-bot-with-full-backtesting-e0e9b12e2155
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-02

## 要約
開発者がフル機能のLLMトレーディングボットをオープンソース公開したGoPenAIブログ記事。
主要機能: ①LLM（GPT/Claude/Llama対応）によるシグナル生成、②バックテストエンジン組み込み（スリッページ・コミッション考慮）、③チェーン・オブ・ソート推論による売買根拠の透明化、④リスク管理層（ポジションサイジング・ストップロス）。
アーキテクチャ: データ取得（OHLCV）→LLM分析プロンプト→JSON出力（action/confidence/reasoning）→バックテスト実行→パフォーマンスレポート。
実験結果: BTC/USDで6ヶ月バックテスト、LLM版が単純移動平均クロスオーバー比で15-20%高いリターン（ただしスプレッド未考慮のケースも）。
GoPenAI Repositoryで公開中、Pythonベース、Alpaca API経由でのライブトレード対応。P-004・P-005のFX自動取引アーキテクチャ参考実装として活用可能。
