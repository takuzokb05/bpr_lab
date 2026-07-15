# 自作LLM プロジェクト

> グローバル設定 `~/.claude/CLAUDE.md` の規約はすべて継承する。本ファイルはこのプロジェクト固有の追記。

## 目的とゴール

学習しながらLLMを内製し、最終的に ai-council（ai-teams のOSS版）へ組み込む。

- **最短ゴール: 2026-07-04 G検定合格**（本日 2026-06-16 時点で残り約18日）
  - 手を動かす学習を通じて検定範囲の概念を定着させるのが第一。
  - 「読んで暗記」ではなく「動かして loss が下がるのを見る」方式。
- **次フェーズ: ai-council 用の内製LLM**
  - G検定で得た知識をそのまま実戦投入へ接続する。
  - 統合先は ai-teams / ai-council（既に **Ollama + Qwen3** で内製LLM路線）。

## 二本立ての方針

| トラック | 目的 | ツール | コスト | カバーする検定論点 |
|---|---|---|---|---|
| **A: 理解の土台**（一から） | Transformerの全工程を自分の手で理解 | nanochat 精読 + rasbt『LLMs-from-scratch』写経 | $0（Colab無料/CPU） | Transformer/Self-Attention/BPE/事前学習/最適化/評価指標 |
| **B: 実戦投入**（既存活用） | ai-council に載せる内製モデル | Unsloth + Qwen3.5 QLoRA微調整 | $0（Colab無料T4） | LoRA/量子化/SFT/転移学習/推論 |

- **線引き**: 「一から事前学習」=トラックA（nanochat/rasbt）。「微調整・量子化・推論」=トラックB（Unsloth）。両方やると G検定範囲がほぼ埋まる。
- **ai-council 統合の本命ルート**: Unslothで人格微調整 → **GGUF出力** → **Ollama** に載せる → ai-council から呼ぶ。追加インフラほぼゼロ。

## nanochat 精読の順路（速習スクリプトの実行順＝読む順）

1. `runs/speedrun.sh` — パイプライン全体の地図
2. `nanochat/tokenizer.py` — BPEトークナイザ
3. `nanochat/gpt.py` — **Transformer本体（最重要・行単位で写経）**
4. `scripts/base_train.py` + `nanochat/optim.py` — 事前学習ループ・AdamW/Muon・損失
5. `nanochat/loss_eval.py` / `core_eval.py` — 評価指標（bits-per-byte）
6. `scripts/chat_sft.py` — SFT（ファインチューニング）
7. `scripts/chat_rl.py` — RL/アライメント
8. `nanochat/engine.py` — 推論・KVキャッシュ

## 環境・コスト制約

- **学習・写経・精読・小実験は Colab 無料枠 / ローカルCPU**で行う（$0）。
- **Colab 無料枠の注意**: アイドル90分 / 最大12hで切断。長時間学習は途中で落ちる前提。
- **クラウドGPU課金（nanochatフル速習の8×H100=$50〜100, RunPod/Lambda等）は、起動前に必ずコスト額を提示して承認を取る**（グローバル規約: 検証段階のコスト発生は事前確認）。
- サブスク稼働中の API 直叩き（Anthropic等）禁止。大量LLM判定はサブエージェント分割。

## 主要リソース

- nanochat: https://github.com/karpathy/nanochat （フルスタック自作LLM、約8000行）
- rasbt『Build a LLM from Scratch』コード: https://github.com/rasbt/LLMs-from-scratch （Colab前提・検定対策の本丸）
- Unsloth: https://github.com/unslothai/unsloth （Qwen3/3.5 無料Colab微調整ノートあり）
- Unsloth Qwen3.5 微調整ガイド: https://unsloth.ai/docs/models/qwen3.5/fine-tune

## 進捗管理

- マイルストーンと完了タスクは本ファイル下部 or `PLANS.md` に追記していく。
- ai-council 側の現状（使用モデル・Ollama呼び出し口）は統合フェーズ着手時に確認する。

### マイルストーン

- [ ] トラックA-1: Colabで nanochat clone + 精読環境
- [ ] トラックA-2: rasbt写経（Transformer/Attention まで）
- [ ] G検定受験（2026-07-04）
- [ ] トラックB-1: Unsloth Qwen3.5 QLoRA 微調整を1周
- [ ] トラックB-2: GGUF出力 → Ollama → ai-council 接続
