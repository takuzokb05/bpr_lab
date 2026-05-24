# MT5×Python×Gemini 生成AIに相場を「思考」させる自動売買システム完全ガイド

- URL: https://note.com/crypto_news_777/n/na64e99262b1a
- ソース: web
- 言語: ja
- テーマ: ai-trading
- 取得日: 2026-05-24

## 要約
Note記事（AI投資予報士@たける）によるMT5×Python×Gemini API統合の自動売買システム構築ガイド。アーキテクチャはMT5（MQL5）でタイマー起動→C++ DLLでMT5-Python間ブリッジ→PythonからGemini APIへプロンプト送信→シグナル返却→MQL5で発注というパイプライン。プロンプト設計（「強気/弱気/中立」3択強制フォーマット）、マーケットデータの前処理（OHLCV+ATR+RSIを構造化テキスト化）、レイテンシ管理（200-2000ms対策としての1時間足以上推奨）を詳述。誇張なしの堅牢なアーキテクチャとして実践的価値が高い。
