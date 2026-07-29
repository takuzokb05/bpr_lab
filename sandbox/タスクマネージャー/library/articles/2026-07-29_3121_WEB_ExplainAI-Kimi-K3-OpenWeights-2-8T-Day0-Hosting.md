# Kimi K3 Open Weights: 2.8T Parameters, Day-0 Hosting — Technical Deep Dive

- URL: https://explainx.ai/blog/kimi-k3-open-weights-2-8-trillion-parameters-july-2026
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-07-29

## 投稿内容

ExplainAI (July 2026): Technical overview of Kimi K3 open-weight model release.

**Release Details**
- Released: July 26, 2026 (early ahead of July 27 announcement)
- 2.8 trillion parameters
- 1,048,576-token (1M) context window
- First open-source model in the 3-trillion-parameter class

**Technical Architecture**
- Sparse Mixture of Experts: 896 experts, only 16 fire per token
- ~50B active parameters per forward pass (economical compute despite 2.8T total)
- Stable LatentMoE architecture
- KDA (Knowledge Distillation Acceleration)
- Quantization-aware training (QAT) throughout
- MXFP4 4-bit precision: ~1.4TB weight file

**Deployment**
- Day-0 hosting: Together AI and Modal
- Self-hosting requires high-end multi-GPU cluster (1.4TB resident)
- Hugging Face: community quantizations available

**Privacy Advantage**
Unlike API access through Moonshot AI (China-based company), self-hosted deployment ensures data never leaves user-controlled infrastructure — significant for enterprise and government use cases.

**Benchmark Position**
Frontier-tier performance across SWE-bench and major reasoning benchmarks, matching or approaching closed models at the frontier while being freely available.

## 要約
ExplainAIによるKimi K3技術詳細。2.8T（MoE: 896専門家中16が発火、実効50B）・1Mコンテキスト・MXFP4 1.4TB。Stable LatentMoE+KDA+QATで2.8T規模を経済的運用可能に。Day-0ホスティング（Together AI/Modal）あり。セルフホスティングにより中国系インフラへのデータ流出を防ぐプライバシー利点を評価。フロンティア級ベンチマーク性能で無償利用可能。
