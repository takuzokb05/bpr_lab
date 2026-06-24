# Step C 完了総括 2026-05-10

> **次回の自分へ**: このファイルだけ読めば 60 秒で Step C 全完了状態が把握できる。
> 詳細は末尾の関連ファイルから辿る。Handover 2026-05-09 (前回中断時点) の更新版。

---

## 30 秒サマリ

SPEC v2 § 2-1 季節判定 **検証完全完了** (2026-05-10)。GBP_JPY 単一通貨で M15+H1 二層の確定値を取得し、`src/spec_v2/seasonal_detection.py` にコード資産化。

- **採用通貨**: GBP_JPY (EUR_USD 除外、USD_JPY 補助候補)
- **層構造**: M15 主層 + H1 主層 (D1 削除)
- **採用閾値**: GBP_JPY M15 YZ_vol > 30%ile / H1 YZ_vol > 0.00175
- **評価指標**: Spearman ρ + block bootstrap CI を主、TR は補助 (新仮説 H9)
- **物語破棄条項**: 発火条件成立だが個別仮説更新で対応 (HYPOTHESES_2-1.md v1.1)
- **次フェーズ**: GBP_JPY ペーパートレード (PoC) 推奨

---

## 完了したタスク (時系列)

### Phase 0: v1 検証 (前回まで)

| ステップ | 内容 | 結果 |
|---|---|---|
| Step A | 仮説台帳 (HYPOTHESES_2-1.md) 起草 | H1〜H8 8 仮説 |
| Step B | 文献調査 4 並列 | H7 ★☆☆ 等の格付け |
| Step C P0-1 | 試行数棚卸し | N=606 |
| Step C P0-2 | Permutation test | 11/12 で p<0.05 |
| Step C P0-3 | 多重補正 12-family | AAA 5 / AA 2 / A 3 / 🔴 2 |
| Step C P1-1 | Mode A WFA (閾値固定) | 9 個 5/5 + 3 個 4/5 |
| Step C P1-1b | Mode B WFA (閾値再選定) | **重大発見**: 11/12 不一致、二極化発生 |
| Step C 新 P0 Q1 v1 | 単峰性検証 (20 分位) | 「単峰確定」と書いたが後にレビューで撤回 |
| Step C 新 P0 Q2 v1 | H1 グリッド拡張 | 「×2.0 が新最良」と書いたが後にレビューで撤回 |

### レビュー (2026-05-10 早朝): 3 観点並列

| レビュワー | 評価 | 主指摘 |
|---|---|---|
| Jenny (実装適合性) | 概ね PASS | バグ 2 件発見 |
| karen (本物度) | 55-60% | 過度な主張、EUR_USD ×2.0 で WFA 崩壊予測 |
| analyst (方法論) | 注意/要再検討 | 介入実験未実施、bootstrap CI 欠如、過去教訓再演 |

### v2 検証 (Step 1-5)

| ステップ | スクリプト | 結果 |
|---|---|---|
| Step 1: バグ修正 | (Edit 2 件) | Q1 三項演算子 / Mode B float 等価性 |
| Step 2: Q1 v2 | `_spec_2_1_indicator_return_curve_v2.py` | 50 分位+bootstrap CI+dip+Spearman → 11/12 弱U字成分支持、「単峰確定」撤回 |
| Step 3: 介入実験 | `_spec_2_1_rolling_wfa_modeB_v2.py` | low 群固定方式で M15 YZ_vol CV 0.51→0.06 → Q1 仮説部分立証 |
| Step 4: 実用性 WFA | `_spec_2_1_h1_practical_wfa.py` | EUR_USD ×2.0 usable 1/5 = karen 指摘的中 |
| Step 5: Q2 v2 | `_spec_2_1_h1_grid_extension_v2.py` | TR 95%CI 重なり多数で「最良」確定不可 |

### Phase 1-3 (本日完了分)

| Phase | タスク | スクリプト/成果物 | 結果 |
|---|---|---|---|
| **P1-A** | Q3 CHOP <25 多重補正 (15-family) | `_spec_2_1_multiple_testing_v2.py` | GBP_JPY のみ p_rw=0.0068 で生存。USD/EUR/D1 全棄却 |
| **P1-B** | 真因補強 (3 候補分離) | `_spec_2_1_root_cause_analysis.py` | グリッド/サンプル/自己相関で「複合構造 4 要素」確定 |
| **P1-C** | 順位ベース代替指標 | `_spec_2_1_rank_based_alternatives.py` | Spearman ρ+block bootstrap が TR より検出力高い (11/12) |
| **P2-A** | EUR_USD 処遇決定 | (判断ドキュメント) | **完全除外** (実用 WFA 崩壊 + 異質性 + CHOP 棄却) |
| **P2-B** | D1 層運命確定 | (判断ドキュメント) | **削除** (15-family 全棄却 + 形状判別困難) |
| **P2-C** | HYPOTHESES 再起草判断 | `HYPOTHESES_2-1.md` v1.1 | 個別仮説更新 (H4 ★★★★★ / H3,H7 反証 / H6 撤回 / 新 H9) |
| **P3-A** | SPEC v2 § 2-1 数値降ろし | `SPEC_v2.md` 確定セクション追加 | GBP_JPY 単一通貨 / 二層 / 評価指標確定 |
| **P3-B** | スクリプト整理 + コード資産化 | `src/spec_v2/seasonal_detection.py` + `__init__.py` | SeasonalDetector クラス (PoC 用) |

---

## 確定結論

### 1. 通貨選択

**GBP_JPY 単一通貨運用** (H4 ★★★★★)

| ペア | 評価 | 判定 |
|---|---|---|
| **GBP_JPY** | 実用 WFA usable 5/5 + n_pass 5/5、TR 高、介入実験で最大 CV 改善 | **主候補 (採用)** |
| USD_JPY | usable 4/5 (fold 1 シビア)、流動性最高、亡き者の世界で運用中 | 補助候補 (別途検証要) |
| EUR_USD | ×2.0 で usable 1/5 (崩壊)、異質性、CHOP 棄却 | **完全除外** |

### 2. 層構造

**二層 (M15 主層 + H1 主層)、D1 削除**

- D1 棄却根拠: P1-A 15-family で 3 ペア棄却 / Q1 v2 形状判別困難 / P1-C CI 幅 3 倍

### 3. 採用閾値 (GBP_JPY)

| 層 | 指標 | 閾値 | 検証根拠 |
|---|---|---|---|
| M15 主層 | YZ_vol(w=14) > 30%ile (ローリング) | 約 0.00039 | P0-3 AAA + Q1 v2 単調支持 + Spearman ρ +0.214 (CI [+0.18, +0.25]) + 介入で CV 0.51→0.06 |
| H1 主層 | YZ_vol(w=20) > 0.00175 (絶対) | 0.00175 | 実用 WFA usable 5/5 + n_pass 5/5、Spearman ρ +0.233 |
| M15 補完 | CHOP(l=14) <25 | 25 | P1-A 15-family p_rw=0.0068 生存だが Spearman ρ -0.06 で効果弱 → オプショナル扱い |

### 4. 評価指標 (新仮説 H9)

**Spearman ρ + block bootstrap CI を主、TR を補助**

- Spearman: 順位ベースで low 群感度なし
- block_size = lookahead × 4 (M15: 96, H1: 24, D1: 20) で自己相関考慮
- TR は実用閾値での効果サイズの目安として補助利用

### 5. 二層一致判定 (本番ロジック)

```python
from src.spec_v2.seasonal_detection import SeasonalDetector, SeasonRegime

detector = SeasonalDetector(pair="GBP_JPY")
judgment = detector.judge(m15_df, h1_df)

if judgment.regime == SeasonRegime.VOLATILE:
    # 二層一致: 高ボラ局面
    # → シグナル生成 (今後の SPEC v2 § 3-1 等で扱う)
    ...
elif judgment.regime == SeasonRegime.CALM:
    # 両層とも条件未達: 静穏
    # → ノートレード
    ...
elif judgment.regime == SeasonRegime.TRANSITIONAL:
    # 片層のみ条件成立: 過渡期
    # → 慎重判断 or ノートレード
    ...
```

---

## 主張の変遷と最終確定

### v1 主張 → v2 検証 → 最終確定

| トピック | v1 主張 | v2 検証で判明 | 最終確定 |
|---|---|---|---|
| 単峰性 | 「12/12 単峰確定、U字 0 件」 | 11/12 で二次係数 a CI 完全正 (弱U字成分) | **「単調 + 弱U字成分」の複合形状** |
| Mode B 二極化の真因 | 「TR 評価式の low 群感度が真因 (確定)」 | M15 で立証、H1/D1 で別要因併存 | **複合構造 4 要素** (単調性 + low 群感度 + 末端最適 + 自己相関) |
| H1 最適閾値 | 「USD/EUR/GBP × 2.0 が新最良」 | TR 95%CI 重なりで統計的差不明確 + EUR_USD WFA 崩壊 | **GBP_JPY ×1.0 (現 SPEC) 維持または ×1.5 慎重採用** |
| D1 棄却の真因 | 「サンプル数不足が真因」 | 形状判別困難 (a CI ゼロ跨ぎ) + 自己相関 | **複数要因、削除推奨** |
| CHOP の有用性 | 「補完層として残す価値あり」 | Spearman ρ -0.02〜-0.06 で効果弱、GBP のみ 15-family 生存 | **オプショナル (実装後 PoC で効果検証)** |
| 評価指標 | 「TR > 1.0 が合格基準」 | TR は low 群感度を持ち脆弱 | **Spearman ρ + block bootstrap が主指標** |

---

## HYPOTHESES_2-1.md の状態 (v1.1)

| 仮説 | v1 強さ | v1.1 強さ | 変化 |
|---|---|---|---|
| H1 (3 状態モデル) | ★★ | ★★ | 未検証で保留 |
| H2 (ボラ × トレンド直交分解) | ★★ | ★★ | 微修正 (単純直交否定) |
| H3 (M15/H1/D1 三層) | ★★ | **★ (反証寄り)** | D1 削除推奨 |
| H4 (ペア別閾値) | ★★★★ | **★★★★★** | 強化 (EUR_USD 異質性決定的) |
| H5 (TR > 1.0 合格基準) | ★★ | ★★ | 補助指標化 |
| H6 (単一 WF) | ★ | **撤回** | 5-fold WFA 採用 |
| H7 (三層生存=採用根拠) | ★★★ | **★ (反証寄り)** | D1 全棄却で概念崩壊 |
| H8 (length 4 点) | ★★ | ★★ | 未検証で保留 |
| **H9 (順位ベース主指標)** | — | **★★★** | 新規 (検証済) |

**反証寄り (★) 件数: 3** (H3, H6 撤回, H7) → 物語破棄条項発火条件 (★以下 3 件) 成立。だが **白紙再起草を回避**、個別仮説更新で対応 (庭師判断 2026-05-10)。

理由: H4 強化と新規 H9 で「前提のすべてが崩れたわけではない」。構造を残しつつ「D1 削除 + 順位ベース主指標」で建て直すほうが知見継承が効く。

---

## SPEC v2 § 2-1 の状態

`SPEC_v2.md` § 2-1 末尾に新セクション「★ Step C 新 P0 v2 完了 — § 2-1 確定値 (2026-05-10)」を追加。
旧テーブル (各ペアの閾値) は **年輪として保持** + 警告注釈で「最新は確定セクション参照」。

確定セクション内容:
1. 単一通貨 GBP_JPY (推奨)
2. 二層構造 (M15+H1、D1 削除)
3. 評価指標 (Spearman ρ 主 / TR 補助)
4. 採用閾値テーブル (4 行)
5. 本番投入条件
6. Step C 完了宣言 (13 タスク全 ✅)

---

## 成果物一覧

### 検証スクリプト (新規 6 本)
- `scripts/_spec_2_1_indicator_return_curve_v2.py` (Q1 v2)
- `scripts/_spec_2_1_rolling_wfa_modeB_v2.py` (介入実験)
- `scripts/_spec_2_1_h1_practical_wfa.py` (実用性検証)
- `scripts/_spec_2_1_h1_grid_extension_v2.py` (Q2 v2)
- `scripts/_spec_2_1_multiple_testing_v2.py` (P1-A Q3)
- `scripts/_spec_2_1_root_cause_analysis.py` (P1-B 真因補強)
- `scripts/_spec_2_1_rank_based_alternatives.py` (P1-C 代替指標)

### 検証データ (新規 7 個)
- `data/spec_2_1_return_curve_v2.json`
- `data/spec_2_1_rolling_wfa_modeB_v2.json`
- `data/spec_2_1_h1_practical_wfa.json`
- `data/spec_2_1_h1_grid_extension_v2.json`
- `data/spec_2_1_multiple_testing_v2.json`
- `data/spec_2_1_root_cause_analysis.json`
- `data/spec_2_1_rank_based.json`

### バグ修正 (Edit 2 件)
- `scripts/_spec_2_1_indicator_return_curve.py` (line 309-311 三項演算子)
- `scripts/_spec_2_1_rolling_wfa_modeB.py` (line 283 float 等価性)

### ドキュメント (新規 + 更新)
- 新規: `docs/vision/research/STEP_C_NEW_P0_VERIFIED_SUMMARY.md` (v2 検証統合)
- 新規: `docs/vision/research/STEP_C_COMPLETION_2026-05-10.md` (本ファイル)
- 更新: `docs/vision/HYPOTHESES_2-1.md` (v1.1 — 個別仮説更新 + H9 追加)
- 更新: `docs/SPEC_v2.md` (§ 2-1 確定セクション追加)
- 更新: `STATUS.md` (新 P0 v2 完了反映)
- 撤回マーク追加: `STEP_C_NEW_P0_1_unimodality_result.md` / `STEP_C_NEW_P0_2_h1_grid_extension_result.md`

### コード資産 (新規)
- `src/spec_v2/__init__.py`
- `src/spec_v2/seasonal_detection.py` (SeasonalDetector クラス + セルフテスト)

### Memory (新規)
- `feedback_intervention_required_for_causation.md` (新教訓: 真因主張は介入実験 / 採用候補は実用 WFA)
- `MEMORY.md` 索引更新

---

## 残課題 (Phase 4 分岐判断)

### 未着手・保留

- **§ 2-2 (HMM レジーム検出)** などの他 14 スキーム検証
- **PoC 実装**: GBP_JPY ペーパートレード環境構築
- **§ 3-1 シグナル生成**: 季節判定 → エントリー判断のロジック設計
- **§ 4-1 朝のセッション (節目モード)**: AI 賢者対話の実装
- **物語破棄条項の追跡**: 次回 v2 検証で更に 2 件以上 ★ 化したら本格的な再起草

### Phase 4 分岐 (推奨: β)

- (α) 他スキーム展開: § 2-2 → § 2-3 と順次検証
- **(β) PoC 実装先行 (推奨)**: GBP_JPY で「季節判定だけ動く戦略」を 1-3 か月走らせる
- (γ) 段階的併合: § 2-2 だけ追加して 2 スキーム揃ってから PoC

推奨理由: ゼロベース再構築の哲学 (生命体・対話・成長) には「動かしながら学ぶ」が合う。PREMISE.md の「実運用で異常検出」も活用できる。

---

## 関連ファイル

### 北極星 (3 点 + 教訓)
- `docs/vision/STORY.md` / `PREMISE.md` / `OPERATING_MODEL.md` (v2.1)
- `docs/vision/_archive/LESSON_*.md` (5 本)

### 仮説台帳
- `docs/vision/HYPOTHESES_2-1.md` v1.1

### 検証ドキュメント (Phase 順)
- `STEP_C_P0_trial_inventory.md` (P0-1)
- `STEP_C_P0_2_random_baseline_result.md` (P0-2)
- `STEP_C_P0_3_multiple_testing_result.md` (P0-3)
- `STEP_C_P1_1_rolling_wfa_result.md` (P1-1)
- `STEP_C_P1_1b_threshold_drift_result.md` (P1-1b)
- `STEP_C_NEW_P0_1_unimodality_result.md` (Q1 v1, ⚠️ 撤回マーク済)
- `STEP_C_NEW_P0_2_h1_grid_extension_result.md` (Q2 v1, ⚠️ 撤回マーク済)
- `STEP_C_NEW_P0_VERIFIED_SUMMARY.md` (v2 統合)
- `HANDOVER_2026-05-09.md` (前回中断時点)
- `STEP_C_COMPLETION_2026-05-10.md` (本ファイル)

### SPEC
- `docs/SPEC_v2.md` § 2-1 (確定セクション追加済)

### 教訓 (memory)
- `feedback_anomaly_is_signal_not_conclusion.md`
- `feedback_assumption_vs_measurement.md`
- `feedback_indicator_validation_pitfalls.md`
- `feedback_intervention_required_for_causation.md` (新, 2026-05-10)
- `project_fx_spec_v2_verification.md`

---

## 再開時の最短ルート

1. 本ファイル (Completion 2026-05-10) を読んで状況把握 (60 秒)
2. **STATUS.md** を読んで構成と進捗確認 (1 分)
3. **Phase 4 分岐判断** (推奨: β PoC 実装)
4. PoC 実装着手なら:
   - `src/spec_v2/seasonal_detection.py` を `main.py` から呼び出す形でラッパー実装
   - GBP_JPY デモ口座でペーパートレード起動
   - シグナル生成ロジック (§ 3-1) を別途検証 → 統合
5. 他スキーム展開なら:
   - `OPERATING_MODEL.md` v2.1 の § 2-2 (HMM) を起点に Step A → B → C を再開

---

## ブランチ・コミット状態

- **ブランチ**: `feature/spec-v2-rebuild` (origin に push 済)
- **直近コミット**: 9043e0a — "セッション中断 — 次回更新用 Handover レポート"
- **本日のコミット**: (これから 1 コミットで Step C 完了をまとめる)

完了。
