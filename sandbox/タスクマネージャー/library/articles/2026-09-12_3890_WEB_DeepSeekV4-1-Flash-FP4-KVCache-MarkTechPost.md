# DeepSeek-V4.1-Flash: 1M Context, FP4 KV Cache & Cross-Layer Attention Reuse (MarkTechPost)

- URL: https://www.marktechpost.com/2026/09/10/deepseek-ai-released-deepseek-v4-1-flash-with-1m-context-fp4-kv-cache-and-cross-layer-attention-reuse/
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-09-12

## 投稿内容
MarkTechPost technical analysis of DeepSeek V4.1-Flash (September 10, 2026). Causal Encoder-Decoder architecture detail: 552B-parameter MoE (activates 8B/16B params per input/output), 1M context, native multimodal, trained from scratch on 45T tokens. FP4 KV cache quantization compresses KV from FP16 to FP4 (1/4 memory), combined with cross-layer attention reuse (sharing attention matrices across multiple layers) to achieve 890 bytes/token global KV cache (1/4 of V4-Flash). Persistent cache footprint reduced to 1/8. Low pricing ($0.15 uncached input, $0.60 output per MTok, MIT open weights) makes the 552B MoE model cost-competitive with smaller dense models.

## 要約
MarkTechPostによるDeepSeek V4.1-Flash（2026-09-10）の技術分析。Causal Encoder-Decoderアーキテクチャ: 552B MoE（入力8B/出力16B活性化）、1Mコンテキスト、ネイティブマルチモーダル、45Tトークンで0から学習。KVキャッシュ圧縮の仕組み: FP4量子化（FP16→FP4でメモリ1/4）とクロスレイヤーアテンション再利用（複数レイヤーでアテンション行列を共有）の組み合わせにより890バイト/トークン（V4-Flashの1/4）を達成。永続キャッシュフットプリントは1/8まで削減。$0.15/MTok（未キャッシュ入力）、$0.60/MTok（出力）、MITオープンウェイトにより552B MoEを小型密結合モデルと同等コストで提供。
