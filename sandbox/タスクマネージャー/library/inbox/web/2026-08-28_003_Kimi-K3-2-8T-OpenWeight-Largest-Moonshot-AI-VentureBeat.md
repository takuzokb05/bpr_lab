# Kimi K3: 2.8兆パラメータ・史上最大オープンウェイトモデル

- URL: https://venturebeat.com/technology/chinas-moonshot-ai-releases-kimi-k3-the-largest-open-source-model-ever-rivaling-top-u-s-systems
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-08-28

## 要約

中国Moonshot AIが2026年7月16日にKimi K3をリリース。2.8兆パラメータのMixture-of-Experts (MoE)アーキテクチャで、史上最大のオープンソースAIモデル。完全な重みは7月27日に公開（Modified MITライセンス、商用利用可）。

**技術仕様**:
- 2.8兆パラメータ（DeepSeek V4 Pro/1.6兆の約75%増）
- 推論時のアクティブパラメータ: ~35B（MoE効率化）
- コンテキスト長: 100万トークン
- 独自アーキテクチャ: Kimi Delta Attention（Kolmogorov-Arnold Dense Attention）+ Attention Residuals
- マルチモーダル対応（ビジュアル理解）・思考モード搭載
- OpenAI SDK互換

**パフォーマンス**:
- GDPval-AA v2: 1,687点（3位、Claude Fable 5 Max・GPT-5.6 Sol Maxに次ぐ）
- AA-Briefcase agentic benchmark: 2位（1,527点）
- BrowseComp情報検索: 91.2/100（SOTAクラス）
- Frontend Code Arena: 1位（Claude Fable 5を上回る）
- 価格: $3/$15 per Mトークン

**意義**: オープンソースのパフォーマンスが独自モデルとの差を実質的に解消した転換点。中国AIエコシステムの国際競争力を示す一方、米国の計算リソース輸出規制の下でも実現。FX自動取引や低コスト推論環境の選択肢として重要。
