# MT5+GPT-4 Python自動売買: OHLCデータ分析→BUY/SELL推奨の実装例（GitHub）

- URL: https://github.com/Tzigger/MT5_trading_bot
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-05-27

## 投稿内容
GitHubで公開されたMT5+GPT-4統合Python自動売買ボット実装プロジェクト。

## 要約
MetaTrader5とGPT-4を統合したトレードシグナル自動生成。OHLCデータとティックデータを分析してリアルタイムBUY/SELL推奨（エントリー・ストップロス・テイクプロフィット含む）を出力。PythonのMetaTrader5ライブラリを使用してMT5ターミナルに接続。関連実装（mt5_live_trading_bot）は6層エントリーフィルター（ATR・Angle・Price・CandleDirection・EMA Ordering・Time）によるエントリー検証、リアルタイムGUI、4フェーズステートマシンを実装。Python+MT5+LLMの組み合わせによるFX自動売買の具体実装参照として有用。LLM部分がGPT-4なのでClaude APIへの置き換えが可能（Claude Agent SDKを使用）。sandbox/FX自動取引/のmain.pyへの応用可能性が高い一次情報。
