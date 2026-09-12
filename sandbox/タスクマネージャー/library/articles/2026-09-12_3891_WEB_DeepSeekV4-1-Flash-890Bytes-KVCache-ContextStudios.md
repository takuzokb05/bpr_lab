# DeepSeek V4.1 Flash: 890 Bytes KV Cache per Token — Technical Deep Dive (Context Studios)

- URL: https://www.contextstudios.ai/blog/deepseek-v4-1-flash-890-bytes-kv-cache-per-token
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-09-12

## 投稿内容
Deep technical analysis of DeepSeek V4.1-Flash's KV cache innovation (Context Studios). Global KV cache: 890 bytes/token, approximately 1/4 of V4-Flash (75% reduction). Persistent cache footprint: ~1/8. Two enabling techniques: (1) FP4 quantization — moves from FP16 to FP4, achieving 4x memory reduction per attention head; (2) cross-layer attention reuse — shares attention matrices across multiple transformer layers, reducing the number of unique KV pairs that need to be stored. Practical implications: dramatically lower serving costs, ability to handle longer contexts on same hardware, larger batch sizes per GPU. The 890-byte figure means a 1M-token context requires roughly 890MB of KV cache, enabling efficient deployment of the 552B model.

## 要約
Context StudiosによるDeepSeek V4.1-FlashのKVキャッシュ革新の技術深掘り。グローバルKVキャッシュ890バイト/トークン（V4-Flashの1/4、75%削減）、永続キャッシュフットプリント約1/8。実現技術の詳細: ①FP4量子化（FP16→FP4でアテンションヘッド毎に4倍メモリ削減）②クロスレイヤーアテンション再利用（複数Transformerレイヤーでアテンション行列を共有し、保存が必要なユニークなKVペア数を削減）。実用的影響: 1Mトークンコンテキストのキャッシュが約890MBと大幅に縮小、同一ハードウェアでの長コンテキスト処理効率向上・大バッチサイズ実現・サービングコスト削減が可能に。
