# Testing LLM-Driven Trading on MetaTrader 5: Experiment Results Jan 2026

- URL: https://medium.com/@thibauld1263/table-of-contents-f92f9ae840de
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-29

## 要約
2026年1月発表のLLM駆動MT5取引実験報告。GPT-4o・Claude 3.5・DeepSeek V3の3モデルをMetaTrader 5に接続し、FX（EUR/USD、USD/JPY）で実際に取引を実行した実験。技術実装：Python Webhookブリッジ経由でMT5 EAとLLM APIを接続、5分足チャートデータ＋ニュースフィードをコンテキストとして渡す。結果：3モデルともランダムウォーク以上のパフォーマンスは統計的に確認できず、取引コスト（スプレッド）の影響が大きい。LLM単体での短期FX取引は困難だが、マルチエージェント構成とファンダメンタルズ分析との組み合わせに可能性を見出す。実装コード含む実践レポート。
