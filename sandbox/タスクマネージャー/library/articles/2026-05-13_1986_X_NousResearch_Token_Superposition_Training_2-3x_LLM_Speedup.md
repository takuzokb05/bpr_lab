# Nous Research、LLM事前学習を2〜3倍高速化するTST手法を発表

- URL: https://x.com/NousResearch/status/2054610062836892054
- ソース: x
- 言語: en
- テーマ: ai-news
- 取得日: 2026-05-13
- いいね: 1611 / RT: 172 / リプライ: 89
- 投稿者: @NousResearch / フォロワー 170,464

## 投稿内容
Today we release Token Superposition Training (TST), a modification to the standard LLM pretraining loop that produces a 2-3× wall-clock speedup at matched FLOPs without changing the model architecture, optimizer, tokenizer, or training data.

During the first third of training, the model reads and predicts contiguous bags of tokens, averaging their embeddings on the input side and predicting the next bag with a modified cross-entropy on the output side. For the remainder of the run, it trains normally on next-token prediction. The inference-time model is identical to one produced by conventional pretraining.

Validated at 270M, 600M, and 3B dense scales, and at 10B-A1B MoE.

## 要約
Nous ResearchがToken Superposition Training（TST）を公開した。これはLLMの標準的な事前学習ループに対する改良手法で、モデルアーキテクチャ・オプティマイザー・トークナイザー・学習データを変更せずに、同等のFLOPsで壁時計時間の2〜3倍の高速化を実現する。270M・600M・3BのDenseスケールおよび10B-A1B MoEで検証済みである。アーキテクチャ変更不要でこれほど大幅な学習効率改善を達成した点は業界的に重要であり、LLM開発コスト削減への貢献が期待される。
