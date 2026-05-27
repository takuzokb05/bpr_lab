# MT5 + GPT-4 自動売買シグナル生成 Python実装

- URL: https://github.com/Tzigger/MT5_trading_bot
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-05-27

## 要約
MetaTrader5とGPT-4を統合したトレードシグナル生成のPythonプロジェクト。OHLCデータとティックデータを分析してリアルタイムのBUY/SELL推奨（エントリー・ストップロス・テイクプロフィットレベル含む）を自動生成。PythonのMetaTrader5ライブラリを通じたMT5ターミナルとの接続を実装。6層エントリーフィルター（ATR・Angle・Price・CandleDirection・EMA Ordering・Time）による検証を実施。リアルタイムGUIと4フェーズステートマシンを実装した実装例も存在（mt5_live_trading_bot）。Python+MT5+LLMの組み合わせによるFX自動売買の実装参照として有用。ただしGPT-4利用のため競合ソリューション（Claude統合版）との比較検討が必要。サンドボックスのFX自動取引プロジェクト（sandbox/FX自動取引/）への応用可能性が高い。
