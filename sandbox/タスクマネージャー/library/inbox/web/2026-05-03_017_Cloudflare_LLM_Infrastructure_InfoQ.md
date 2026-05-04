# Cloudflare Builds High-Performance Infrastructure for Running LLMs

- URL: https://www.infoq.com/news/2026/05/cloudflare-llm-infrastructure/
- ソース: web
- 言語: en
- テーマ: ai-news
- 取得日: 2026-05-03

## 要約
Cloudflare の LLM 推論インフラ最適化の技術詳細（InfoQ, 2026年5月）。主な技術：①プリフィルとデコードを異なるマシンに分離（入力処理と出力生成を専門化）②カスタム推論エンジンによるGPU効率化③トークン対応負荷分散。具体的成果：Llama 4 Scout を H200 GPU 2枚で稼働、Kimi K2.5 を H100 GPU 8枚で稼働（KVキャッシュ用メモリを確保しながら）。Unweight: モデル重みを15〜22%圧縮し精度損失なし（GPUがロード・移動するデータ量を削減）。Project Think でエージェント向けAIプラットフォームを構築中。グローバルネットワーク上でのエッジAI推論インフラとして注目。
