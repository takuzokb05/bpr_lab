# Kimi K3: 2.8兆パラメータ・史上最大オープンウェイトモデル、独自モデルと実質同等の性能

- URL: https://venturebeat.com/technology/chinas-moonshot-ai-releases-kimi-k3-the-largest-open-source-model-ever-rivaling-top-u-s-systems
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-08-28

## 投稿内容
VentureBeat reports on Moonshot AI's Kimi K3 release (July 16, 2026; full weights July 27, 2026).

**Scale**: 2.8 trillion parameters MoE architecture, the largest open-source AI model ever. Approximately 75% more parameters than DeepSeek V4 Pro (1.6T). ~35B active parameters during inference.

**Architecture**: Kimi Delta Attention (KDA, Kolmogorov-Arnold Dense Attention hybrid linear mechanism) + Attention Residuals—both previously published as open research. 1M token context window. Native vision. Thinking mode. OpenAI SDK compatible.

**Benchmarks**:
- GDPval-AA v2: 1,687 points (3rd, behind Claude Fable 5 Max and GPT-5.6 Sol Max)
- AA-Briefcase agentic benchmark: 2nd place (1,527 points)
- BrowseComp information retrieval: 91.2/100 (state-of-the-art)
- Arena.AI Frontend Code Arena: 1st (ahead of Claude Fable 5)

**License**: Modified MIT, permissive enough for commercial use.

**Pricing**: $3/$15 per M tokens.

**Significance**: A watershed moment where open-source performance has "functionally closed" the gap with proprietary frontier models. Achieved despite US compute export restrictions targeting China.

## 要約
中国Moonshot AIのKimi K3（2026年7月16日発表、7月27日重み公開）。2.8兆パラメータMoEで史上最大のオープンウェイトモデル。DeepSeek V4 Pro（1.6兆）比約75%増のスケール、推論時アクティブは約35B。アーキテクチャは独自のKimi Delta Attention（Kolmogorov-Arnold Dense Attention）+Attention Residualsを採用。1Mトークンコンテキスト・マルチモーダル対応・思考モード搭載・OpenAI SDK互換。ベンチマーク：GDPval-AA v2は3位（Claude Fable 5 Maxのみ上位）、Frontend Code Arenaは1位（Fable 5を上回る）。Modified MITライセンスで商用利用可。価格$3/$15/Mトークン。「オープンソースが独自モデルとの差を実質解消した転換点」とVBは評する。米国の計算リソース輸出規制下でも実現したことが特筆に値する。FX自動取引での低コスト推論選択肢として重要。
