# MT5×Python×Gemini 生成AIに相場を「思考」させる自動売買システム完全ガイド

- URL: https://note.com/crypto_news_777/n/na64e99262b1a
- ソース: web
- 言語: ja
- テーマ: ai-trading
- 取得日: 2026-05-24

## 要約
MT5×Python×Gemini API統合の自動売買システム構築ガイド（note/AI投資予報士@たける）。アーキテクチャはMT5(MQL5)でタイマー起動→C++ DLLでMT5-Python間ブリッジ→PythonからGemini APIへプロンプト送信→シグナル返却→MQL5で発注のパイプライン。プロンプト設計の核心は「強気/弱気/中立」3択強制フォーマット（自由記述を排除してハルシネーション対策）、OHLCV+ATR+RSIを構造化テキスト化するマーケットデータ前処理、200-2000msレイテンシ対策としての1時間足以上推奨。C++ DLLブリッジを使うため他LLM（Claude等）への差し替えが容易な設計も特徴。
