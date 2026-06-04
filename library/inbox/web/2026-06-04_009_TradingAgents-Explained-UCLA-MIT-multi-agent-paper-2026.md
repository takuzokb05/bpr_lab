# TradingAgents Explained: UCLA+MITマルチエージェント取引論文の技術解説

- URL: https://beginnersinai.org/tradingagents-explained/
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-04

## 要約
UCLA+MITチームが発表したTradingAgents論文の技術解説（Beginners in AI）。7エージェント構成の詳細：市場アナリスト（価格・テクニカル）、ソーシャルアナリスト（ニュース・感情）、ファンダメンタルアナリスト（財務指標）、ブルリサーチャー、ベアリサーチャー（対立論証生成）、トレーダー、リスクマネージャー。各エージェントが「チャレンジ・サポート」を繰り返してコンセンサスに到達するメカニズムを図解。バックテスト詳細：AAPL対象で2024年6〜11月、+26.62%累積リターン（BaH対比）、Sharpe 5〜8は論文自身が統計的異常値として明示。GitHub 51,300★・9,300 forks（2026年4月）。コスト：1取引決定=11 LLM呼び出し+20ツール呼び出し（$0.5〜$2）。Claude・GPT・Gemini・Grokをバックエンドとして選択可能。
