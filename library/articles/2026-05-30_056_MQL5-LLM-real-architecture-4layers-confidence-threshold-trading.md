# MQL5 + LLM 2026年実用アーキテクチャ: 4層マイクロサービス・信頼度0.75超で勝率61.7%

- URL: https://www.mql5.com/en/blogs/post/769403
- ソース: web
- 言語: en
- テーマ: ai-trading
- 取得日: 2026-05-30

## 投稿内容
MQL5 + LLM in 2026: The Real Architecture That Works — MQL5 Traders' Blogs, April 29, 2026. Problem: 340+ "AI-branded" Expert Advisors in the MQL5 marketplace are fake — traditional RSI/Bollinger Band logic with AI marketing labels. Real LLM integration requires a four-layer microservices approach: (1) Data Collection Layer (MQL5 EA): serialize OHLCV data, indicators, account state, session context to JSON; (2) Middleware (Python/FastAPI): poll market data, construct prompts, async LLM call, strict JSON schema validation; (3) LLM Inference: GPT-4o, Claude, or local models (Mistral/Llama via Ollama); (4) Execution Gateway (MQL5): confidence-based position sizing. Confidence thresholds — below 0.55: no entry (48.3% win rate), 0.55–0.75: reduced positions, 0.75+: full size (61.7% win rate). Stateful context retaining 5-10 prior decisions, multi-model consensus, adversarial testing, audit trails for compliance. Not suitable for HFT/scalping (1-3s API latency); optimal for higher-timeframe directional filters.

## 要約
MQL5コミュニティの実践エンジニアが市場に出回る「AI詐称EA」340本超を批判し、本物のLLM統合アーキテクチャを公開（2026年4月29日）。4層マイクロサービス構成：データ収集（MQL5 EA・JSON化）→ミドルウェア（Python/FastAPI・スキーマバリデーション）→LLM推論（GPT-4o/Claude/Ollama）→実行ゲートウェイ（信頼度ベースポジションサイジング）。信頼度閾値の実証値：0.55未満ノーエントリー（勝率48.3%）、0.75超でフルサイズ（勝率61.7%）という定量的結果を公開。直近5-10決定を保持するステートフルコンテキスト、マルチモデルコンセンサス、規制対応監査証跡も実装。HFT不適（API遅延1-3秒）、上位時間足方向フィルターとして最適。FX自動取引システム設計の具体的数値・アーキテクチャを示す希少な一次情報。
