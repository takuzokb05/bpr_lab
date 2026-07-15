# Open-Source LLM Trading Bot with Full Backtesting 公開 — CoT推論・リスク管理統合

- URL: https://blog.gopenai.com/i-just-released-an-open-source-llm-trading-bot-with-full-backtesting-e0e9b12e2155
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-02

## 投稿内容
開発者がGoPenAIブログでフル機能のLLMトレーディングボットをオープンソース公開した記事。

**主要機能**
- LLM対応: GPT/Claude/Llama切り替え可能
- バックテストエンジン組み込み（スリッページ・コミッション考慮）
- Chain-of-Thought推論による売買根拠の透明化
- リスク管理層（ポジションサイジング・ストップロス・ドローダウン制限）

**アーキテクチャ**
```
OHLCVデータ取得 → LLMプロンプト構築 → 
JSON出力（action/confidence/reasoning） → 
バックテスト実行 → パフォーマンスレポート
```

**出力JSONフォーマット**
```json
{
  "action": "BUY"|"SELL"|"HOLD",
  "confidence": 0.0-1.0,
  "reasoning": "Chain-of-Thought推論テキスト",
  "position_size": 0.0-1.0
}
```

**実験結果**
BTC/USDで6ヶ月バックテスト: LLM版がSMA-crossover比で15-20%高いリターン
（注: スプレッドやスリッページを完全に考慮していないケースあり）

**ライブトレード**
Alpaca API経由でのライブトレード対応。Paper tradingモードで検証可能。

P-005（MT5+Python+LLMパイプライン）の参考実装として直接活用可能。

## 要約
GoPenAIブログで公開されたオープンソースLLMトレーディングボットの実装詳細記事。GPT/Claude/Llama対応、バックテスト組み込み（スリッページ・コミッション考慮）、Chain-of-Thought推論、ポジションサイジング・リスク管理を統合。
出力JSONは{action, confidence, reasoning, position_size}形式で、P-014（信頼度閾値0.55/0.75）と互換する設計。
BTC/USDバックテストでSMAクロスオーバー比15-20%高いリターン（ただしコスト考慮に注意）。Alpaca API経由でライブトレード対応。
アーキテクチャ（OHLCV→LLMプロンプト→JSON→バックテスト）がP-005（MT5+Python+LLMパイプライン）の参考実装として直接活用可能。
P-026（バックテストへのスプレッド・スリッページ・コミッション統合）の重要性を再確認する実例でもある。
