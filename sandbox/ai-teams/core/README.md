# core/ — AI Teams v3 討論エンジン（UI 非依存）

v2 の2大バグ（人格混線 / 沈黙）を**設計で**根治した、UI から独立した討論オーケストレーター。
設計根拠は `../REBUILD_PLAN.md`（4.5節）と `../RESEARCH_2026-05_orchestration.md`。

## 構成

| ファイル | 役割 |
|---|---|
| `personas.py` | ペルソナ・レジストリ（dataclass + YAML ローダ）。人格はコードでなくデータ |
| `llm_client.py` | LLM 統一 IF。`AnthropicClient`（本番）/ `MockLLMClient`（テスト・APIキー不要） |
| `context.py` | **混線対策の核**: 自分=`assistant` / 他者=【名前】付き`user` でコンテキストを組む |
| `orchestrator.py` | `Council`（進行）+ `RoundRobinScheduler`（沈黙対策）+ `Turn` |

## 2大バグの根治ポイント

- **人格混線** → `build_context()` が、発言生成するペルソナから見て自分の過去発言だけを
  `assistant`、他者を `user`（【名前】付き）にする。v2 の「stopシーケンス境界切り」を廃止。
- **沈黙** → 発言順は LLM でなく `RoundRobinScheduler` が決め、各ラウンドで全パネリストが
  必ず1回発言する。司会の指名には依存しない。
- **均質化（collapse）** → ペルソナ毎に `model` / `temperature` を変えられ、毎ターン反同調
  プロンプトと system 再注入を行う。

## 使い方

```python
from core import Council, AnthropicClient, load_personas

personas = load_personas("personas")            # YAML を読む
council = Council(personas, AnthropicClient())   # 本番 LLM
for turn in council.run("議題テキスト"):          # Turn を逐次 yield
    print(turn.speaker_name, turn.content)
```

テスト/疎通（API キー不要）:

```bash
python3 tests/run_tests.py   # 混線・沈黙・モデル上書きを検証（全 pass）
python3 demo.py              # YAML ペルソナでモック進行を表示
```
