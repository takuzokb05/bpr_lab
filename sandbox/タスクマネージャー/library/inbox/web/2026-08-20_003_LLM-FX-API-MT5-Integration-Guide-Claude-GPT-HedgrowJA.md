# LLM × FX API × MT5 連携ガイド：Claude/GPTをMT5に繋ぐ3つの実装手順

- URL: https://media.hedgrow.io/ja/fx/articles/llm-fx-api-mt5-renkei
- ソース: web
- 言語: ja
- テーマ: ai-trading
- 取得日: 2026-08-20

## 要約

hedgrow mediaによるLLMとMetaTrader5（MT5）を連携してFX自動売買に活用するための実装ガイド（JA）。

3つの接続方式を体系的に整理: ①**ファイルベース連携（最シンプル）** — PythonがLLMシグナルをJSONファイルに書き出し、MT5（MQL5）が定期ポーリングで読み込む方式。レイテンシは数秒〜数十秒。②**Pythonミドルウェア（HTTPサーバー）** — FastAPIサーバーがMT5からのリクエストを受け取り、Claude API等に問い合わせてフィルタリング済みシグナルを返す方式。レイテンシは数百ms〜秒単位。③**直接MQL5 WebRequest** — MQL5からClaude APIへ直接HTTPリクエストを送る方式。最もレイテンシが低いがブローカーのホワイトリスト設定が必要。LLMの役割はテクニカルシグナルの「フィルター」であり主要ロジックではない、APIキーはMQL5ソース内にハードコードしない、バックテスト環境ではソケット通信不可などの実践的注意事項も網羅。コスト制御にはキャッシュとレート制限の実装を推奨。
