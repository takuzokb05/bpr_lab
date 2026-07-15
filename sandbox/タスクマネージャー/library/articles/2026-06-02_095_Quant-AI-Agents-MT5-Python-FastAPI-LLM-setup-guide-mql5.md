# Quant AI Agents MT5 Complete Setup Guide — Python FastAPI + LLM統合 (mql5.com)

- URL: https://www.mql5.com/en/blogs/post/770122
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-06-02

## 投稿内容
MQL5コミュニティブログによるQuantAI Agents（MT5対応）の完全セットアップガイド（2026年5月18日）。

**システム構成**
```
MT5ターミナル
  └── MQL5 ブリッジEA
       └── Python FastAPIサーバー
            └── LLM層（Claude/GPT/Gemini切り替え可）
                └── Webダッシュボード（監視・調整）
```

**セットアップ手順**
1. MT5ターミナルでアルゴリズム取引を有効化
2. Python環境構築（`pip install fastapi uvicorn anthropic`）
3. `.env`にAPIキー設定（`ANTHROPIC_API_KEY`等）
4. FastAPIサーバー起動（`python server.py --port 5000`）
5. MT5にブリッジEAをアタッチ
6. EAパラメータにサーバーURL・LLMプロバイダーを設定

**LLMシグナルフォーマット**
```json
{
  "signal": "BUY"|"SELL"|"HOLD",
  "confidence": 0.0-1.0,
  "sl": 1.0850,
  "tp": 1.0920,
  "lot": 0.1
}
```

**ハイブリッド分析**
ML（機械学習センチメント分析）+ LLM（包括的判断）を組み合わせた二段階シグナル生成。

P-013（MetaTrader MCPサーバー）と組み合わせることでClaude Desktop→MT5の完全な自然言語制御パイプラインが実現可能。

## 要約
MQL5コミュニティブログのQuantAI Agents MT5 完全セットアップガイド（2026年5月18日）。MT5ブリッジEA（MQL5）→Python FastAPIサーバー→LLM層（Claude/GPT/Gemini切り替え可）→Webダッシュボードの4層構成を詳細に解説。
出力JSONは{signal, confidence, sl, tp, lot}形式で、直接MT5のEAが注文を発行できる実装例。
ML（機械学習センチメント）とLLM（包括判断）のハイブリッド二段階シグナル生成アーキテクチャ。
P-013（MetaTrader MCPサーバー）・P-014（4層アーキテクチャ・信頼度閾値）の具体的な実装例として高い実践価値。
セットアップ手順が完全に公開されており、sandbox/FX自動取引/のPythonコードベースへの統合が実現可能。
