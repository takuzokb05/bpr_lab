# Phase 2 第1サイクル 集計レポート — 5候補 BT 結果

**作成日**: 2026-05-26
**対象**: `docs/proposals/REVIEW_SUMMARY.md` 案B 5候補 (#1, #2, #12, #14, #15)
**Phase 2 計画**: `docs/PHASE_2_PLAN.md` (PF≥1.3 / Sharpe≥0.8 / OOS≥30 / 機会費用超過)
**判定**: **5/5 FAIL** → 第2サイクル「signal_v2 + LLM 補完」へ移行 (`docs/CYCLE2_PLAN.md`)

---

## TL;DR

- **5/5 候補すべて Phase 2 BT で FAIL** (PF≥1.3 ゲートを達成した候補: **0**)
- 5候補の実 BT PF レンジ: **0.36 (#15 EUR_USD) 〜 1.169 (#14 USD_JPY Optuna OOS)**、いずれも Gate 1.3 未達
- Phase 0 起草者自己採点平均 **83/100** vs 実 BT PF 平均 **0.83**。「採点が実 PF を予測できない」を **N=5 で定量実証**
- **第2サイクル**: 新規候補を立てるのではなく、既知の `signal_v2` (PF 0.95) を LLM フィルタで補完する方向へ転換 (CYCLE2_PLAN.md)

---

## 1. 5候補 詳細結果テーブル

| 候補 | 戦略タイプ | Phase 0 自己採点 | Phase 1 6評価委員 | Phase 2 BT 結果 (主要指標) | ゲート判定 |
|---|---|---:|---|---|:---:|
| **#1 EUR_USD H1 RSI Pullback** | 平均回帰 | **87/100** | **6/6 PASS (全員)** | 全期間 PF **1.09**, OOS PF **0.57**, OOS Sharpe **-2.47**, OOS trades 29 (<30), self-improvement 無効化時の素 PF **0.79** / 5年 **-481k JPY** | **FAIL** |
| **#2 USD_JPY M15 RSI Pullback** | 平均回帰 | 79/100 | 5/6 PASS (history 条件付) | 2年 M15 PF **0.699**, Sharpe -1.65, 累計 **-8,875 JPY**, 年率 **-0.44%** / 同期間 H1 PF 0.587 → **timeframe 特異性 refuted** | **FAIL** |
| **#12 Cointegration Pairs** | 統計的裁定 | 82/100 | **6/6 PASS / risk TOP1** | 5.5年 PF **0.753**, Sharpe **-0.241**, MaxDD **-37.8%**, 累計 **-284,383 JPY**, OOS trades 24 (<30), 最高 coint 維持率の NZD/CAD が最大損失源 | **FAIL** |
| **#14 London Breakout Adaptive** | ブレイクアウト | 82/100 | 4/6 PASS | Optuna OOS PF (3ペア): GBP_USD **0.907** / EUR_USD **0.798** / USD_JPY **1.169**、3ペア合算年率 **-0.34%**、5年累計 **-20,497 JPY** | **FAIL** |
| **#15 Meta-Labeling Ensemble** | ML (Lopez de Prado) | 85/100 | **5/6 PASS / history TOP 10/10** | 5年 ALL PF **0.79**, Sharpe **-0.89**, RF OOS AUC **0.504 (EUR) / 0.485 (UJ)** = ランダム以下, Safe Mode が Primary の 70% を棄却, WFA 30 windows 中 PF≥1.3 は 5 (16.7%) | **FAIL** |

**集計**:
- PF≥1.3 を達成した候補: **0/5**
- Sharpe≥0.8 を達成した候補: **0/5** (#14 USD_JPY のみ年率 Sharpe +1.04 だが PF 1.17 で Gate 未達)
- OOS trades≥30 を達成した候補: **3/5** (#1 と #12 が OOS<30 で FAIL)
- 機会費用 (米国債 4%/年) を超過した候補: **0/5**
- 全必須ゲート PASS: **0/5**

---

## 2. 構造的失敗パターン (5つの教訓)

第1サイクル 5/5 FAIL で確認された、Phase 0 採点フレームを Goodhart 化していた構造的バグ。

### パターン1: 自己採点と実 BT PF の予測力ゼロ

Phase 0 G0/G1/G2 合計の起草者自己採点 (平均 83/100) は、Phase 2 実 BT PF (平均 0.83) を **予測できなかった**:

| 候補 | 自己採点 | 実 BT PF (主要指標) |
|---|---:|---:|
| #1 | 87 | 1.09 (素 0.79) |
| #2 | 79 | 0.70 |
| #12 | 82 | 0.75 |
| #14 | 82 | 0.91 (3ペア平均) |
| #15 | 85 | 0.79 |
| **平均** | **83** | **0.83** |

採点項目を満たすこと自体が「点を取る」最適化対象になり、実エッジの有無と分離された (= **Goodhart 化**)。
→ `feedback_self_rating_predictive_failure.md`

### パターン2: self-improvement のシグナル抑制で見かけ PF が上がる罠

#1 EUR_USD H1 RSI で確認:
- `high_vol regime` 抑制が **5年間で 427回 出入り** = ほぼ常時抑制状態
- 元シグナル 922 件のうち実トレード化 **33件 (3.6%)** = **96.4% シグナル抑制**
- 結果: 抑制あり PF **1.09** (見かけ上達成) vs **抑制なし 素 PF 0.79**

「自己改善が機能した結果としてのプラス」ではなく「**シグナルが大半抑制されたから損失が見えなかった**」だけで、エッジ実証にはなっていない。
→ `feedback_self_improvement_signal_suppression_trap.md`

### パターン3: 統計的妥当性 ≠ 経済的妥当性

#12 Cointegration で確認:
- 最も coint 維持率の高いペア (NZD/USD ↔ USD/CAD, 21.6%) が **最大の損失源** (5.5年 -189,618 JPY)
- 「p<0.05 で cointegration あり」 ≠ 「mean reversion で稼げる」
- 平均勝ち 21k vs 平均負け 36k のペイオフ 0.59 が PF<1 の真因

#15 Meta-Labeling で確認:
- RF OOS AUC 0.504 / 0.485 = **ランダム以下**
- Lopez de Prado / Hudson & Thames の文献値 (Sharpe 0.5→1.2) は再現せず
- 「statistical procedure が完成しているか」と「経済的に稼げるか」は別軸

Pragmatist 撤退教訓 ([[feedback-verification-scope-mismatch]]) の「30秒の BT が複雑な手続き全部に勝つ」を **5回連続で実証**。
→ `feedback_statistical_significance_not_economic.md`

### パターン4: Phase 0 BT グリッド (yfinance + 小サンプル) は偽陽性量産装置

#2 USD_JPY M15 RSI で確認:
- Phase 0 グリッド: yfinance M15 **60日**データ、OOS **n=11**, グリッド OOS PF **2.46** が「最頻パラメータ」と評価
- Phase 2 BT: MT5 M15 **2年**実データ、OOS **n=67**, 実 PF **0.699**
- 同戦略を H1 5年で BT すると PF 0.65 → **timeframe 特異性は実証できず refuted**

#1 EUR_USD H1 RSI でも類似:
- Phase 0 グリッド「最頻パラメータで PF 1.34-1.49」 → Phase 2 BT で OOS PF 0.57
- 起草者は **既存 `backtest_grid_h1_EUR_USD.csv` を流用**して自前 BT を経ていなかった (G0-A 自前BT強制が機能していなかった)

→ `feedback_phase0_bt_grid_unreliable.md`

### パターン5: 「Black Swan 5/5 検証済」と書けても実態は 2/5 程度

全候補で MT5 ブローカー提供データの下限が 2020-10-14 (#12) or 2021-05-07 (#1, #2, #14, #15) のため、要求 5 事象のうち以下が **物理的に検証不能**:
- 2015 SNB ショック (全候補で検証不能)
- 2016 Brexit (全候補で検証不能、#14 GBP_USD の最大テールリスクなのに未検証)
- 2020 COVID 暴落 (全候補で検証不能)

検証できたのは 2024 円介入 / 2024 円キャリー巻き戻しの 2 事象のみ。さらに、戦略が「動かなかった」/「Safe Mode で全棄却」など **「耐性がある」ではなく「参加していなかった」だけ**のケースが大半。

---

## 3. Phase 0 採点フレームの予測力検証

### 起草者自己採点 vs 実 BT PF (Spearman 相関)

| 候補 | 自己採点 | 実 BT PF |
|---|---:|---:|
| #1 | 87 | 1.09 |
| #15 | 85 | 0.79 |
| #12 | 82 | 0.75 |
| #14 | 82 | 0.91 |
| #2 | 79 | 0.70 |

- 採点順位 (#1 > #15 > #12=#14 > #2) と PF 順位 (#1 > #14 > #15 > #12 > #2) は **大きく食い違う**
- 採点最高 (#1, 87) は PF 最高 (1.09) と一致するが、これは self-improvement 抑制の見かけ効果
- 素の PF (抑制なし) で比較すると #1 = 0.79 となり、5候補すべて PF<1.0 で **ほぼ同水準の負け**

### 6評価委員 PASS 数と実 BT PF

| 候補 | PASS 数 | 実 BT PF |
|---|---|---:|
| #1 | 6/6 | 1.09 (素 0.79) |
| #15 | 5/6 | 0.79 |
| #12 | 6/6 | 0.75 |
| #14 | 4/6 | 0.91 |
| #2 | 5/6 | 0.70 |

- 6/6 PASS でも実 BT PF 0.75-1.09 = **ゲート 1.3 未達**
- 評価委員数 (PASS) と実 PF の相関も低い (#14 4/6 PASS が #15 5/6 PASS より上)
- meta 委員が指摘した「採点フレーム Goodhart 化」が **N=5 で実証された**

### 結論

Phase 0 起草者自己採点も、6評価委員 PASS 数も、**実 BT PF を予測する力を持たない**。

これは「Phase 0 採点フレーム自体が Goodhart 化していた」ことの直接実証であり、第2サイクル以降は **採点ではなく PF 差分 (実 BT の絶対値) を絶対基準** とする必要がある (CYCLE2_PLAN.md の方針)。

---

## 4. 各候補の決定打となった発見

### #1 EUR_USD H1 RSI Pullback
- self-improvement の `high_vol regime` 抑制が **5年で 427回 発火**、シグナル 922件中 33件 (3.6%) のみ実トレード化
- 抑制なし素の戦略 PF **0.79 / 5年累計 -481,204 JPY**。「PF 1.09」は抑制の副作用
- WFA 7 windows 中 PF≥1.3 PASS は 1/7 (14%)、W2 (2022年末ECB急利上げ) のみで他全敗
- パラメータ感度 ±20% で **6/6 全 FAIL** = isolated spike (plateau なし)

### #2 USD_JPY M15 RSI Pullback
- Phase 0 グリッドの「OOS PF 2.46」は yfinance 60日 × OOS n=11 のノイズ
- 実 BT (MT5 2年 OOS n=67) で PF 0.699、同戦略を H1 5年で BT しても PF 0.65 = **timeframe 特異性 refuted**
- 「H1 で大負け / M15 で勝つ」の Phase 0 主張は否定 = 戦略本体に欠陥
- 9 パラメータ variant すべて PF<1.0 (仮説空間を埋め尽くした)

### #12 Cointegration Pairs
- 最高 coint 維持率の NZD/USD ↔ USD/CAD ペアが **最大の損失源 (-189,618 JPY)**
- 「方向中立 = 分散源」の理論は正しいが、**負の期待値の戦略は分散源にならない**
- 1トレード最大損失 -137,985 JPY (元本の **13.8%**) = 1% 上限を 13.8倍 超過
- パラメータ感度の最良 (pval_loose で PF 1.26) ですら Gate 1.3 未達

### #14 London Breakout Adaptive
- Optuna 月次最適化で学習 PF → OOS PF が **20-25% 劣化** = 過適合実証
- 主役 GBP_USD で PF 0.91、EUR_USD で 0.80、USD_JPY のみ 1.17 (これも過適合)
- 「実装最速」≠「採用最速」: スピード優先のシンプル手法は誰でも実装可能でエッジが裁定済み
- Brexit (本戦略主役通貨 GBP の最大テールリスク) は 5年データで検証不能

### #15 Meta-Labeling Ensemble
- **RF OOS AUC 0.504 / 0.485 = ランダム以下** = Secondary が Primary シグナルを区別できていない
- Safe Mode (proba<0.6) が Primary 発火 3,818件のうち **70% を棄却**、残り 30% も EUR 勝率 20.7% で **Primary より悪化**
- Hudson & Thames の Sharpe 0.5→1.2 改善は再現せず ("Not a Silver Bullet" QuantConnect 警告の通り)
- 特徴量に「現在のレジーム」「将来 TP/SL 到達への新情報源」がなく、過去価格情報の組み換えのみ

---

## 5. 第2サイクルへの引き継ぎ事項

`docs/CYCLE2_PLAN.md` (signal_v2 + LLM 補完) で活かす Phase 1 教訓:

| 教訓 | 第2サイクルでの実装 |
|---|---|
| 自己採点は予測力なし | 採点を採用しない。**PF 差分のみを絶対基準** |
| ML が数値特徴量から新情報を引き出せない (#15) | LLM で **非数値情報** (ニュース、コンテキスト) を加える |
| Phase 0 BT グリッド (yfinance + 小サンプル) は偽陽性 (#1, #2) | **既知の signal_v2 (PF 0.95) をベース**にして新規 BT グリッド回避 |
| self-improvement のシグナル抑制罠 (#1) | **LLM REJECT 率を必ず可視化**、抑制トレードも別途記録 |
| 統計的妥当性 ≠ 経済的妥当性 (#12, #15) | 統計指標は補助、**PF 差分のみ測定** |
| 負の期待値戦略は分散源にならない (#12) | PF 0.95 単独で分散源にしない、**補強対象として扱う** |
| Black Swan 5/5 検証は実態 2/5 (全候補) | 5年データでは検証不能を honest に明記、必要なら 10年データへ拡張 |

加えて、**「フレーム Goodhart 化」の構造的回避** として、第2サイクルでは「新規候補を立てる前に既知の弱戦略 (signal_v2) を補完できるか」を先に検証する設計。新候補の自己採点で 80+ を取りに行く競争を止める。

---

## 6. ゲート判定サマリ (5候補横並び)

| ゲート項目 | 基準 | #1 | #2 | #12 | #14 (3ペア合算) | #15 (ALL) |
|---|---|---|---|---|---|---|
| PF (full / OOS) | ≥1.3 | 1.09 / **0.57** | **0.70** | **0.75** | 0.91 (Optuna OOS) | **0.79** |
| Sharpe (年率) | ≥0.8 | 0.48 | -1.65 | -0.24 | -0.34/y 換算 | -0.89 |
| OOS trades | ≥30 | **29** | 67 | **24** | 1,423 (3ペア計) | 203 |
| 機会費用 (米国債 4%) | 超過 | +0.73%/y | -0.44%/y | -1.0%/y | -0.34%/y | -0.26%/y |
| 日次/月次損失上限 作動 | 実装+作動 | 実装、軽作動 | 実装、0回 | 実装、4回 | 実装、0回 | 実装、0回 |
| Black Swan キルスイッチ 5/5 | 5事象検証 | 2/5 + 3/5 期間外 | 0/5 + 5/5 不能 | 0/5 + 5/5 不能 | 2/5 + 3/5 期間外 | 0/5 + 5/5 不能 |
| 自己改善メカニズム 実証 | 作動 | 過敏で戦略殺害 | 即停止判定 | 部分実装、効果なし | 動作、過適合 | 動作、エッジ学習不可 |
| **総合判定** | — | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |

---

## 7. 関連ファイル

### Phase 2 BT レポート (5候補)
- `docs/proposals/phase2/1_eurusd_h1_rsi_BT_REPORT.md`
- `docs/proposals/phase2/2_usdjpy_m15_rsi_BT_REPORT.md`
- `docs/proposals/phase2/12_cointegration_BT_REPORT.md`
- `docs/proposals/phase2/14_london_breakout_BT_REPORT.md`
- `docs/proposals/phase2/15_meta_labeling_BT_REPORT.md`

### BT スクリプト
- `scripts/_phase2_bt_1_eurusd_h1_rsi.py`
- `scripts/_phase2_bt_2_usdjpy_m15_rsi.py`
- `scripts/_phase2_bt_12_cointegration.py` + `_phase2_bt_12_diag.py`
- `scripts/_phase2_bt_14_london_breakout.py`
- `scripts/_phase2_bt_15_meta_labeling.py`

### BT 結果データ (主要)
- `data/_phase2_bt_1_eurusd_*.csv` (trades / monthly / stress / wfa / sensitivity / summary.json)
- `data/_phase2_bt_2_usdjpy_*.csv` (同上)
- `data/_phase2_bt_12_cointegration_*.csv` (trades / monthly / stress / wfa / sensitivity / pairs / summary.json)
- `data/_phase2_bt_14_london_*.csv` (trades / monthly / stress / optuna / sensitivity / summary.json)
- `data/_phase2_bt_15_meta_*.csv` (trades / monthly / stress / wfa_eu / wfa_uj / features / labels / summary.json)

### Phase 0 候補書 (5件)
- `docs/proposals/phase0/memory_eur_usd_h1_rsi_pullback.md`
- `docs/proposals/phase0/memory_usd_jpy_m15_rsi_pullback.md`
- `docs/proposals/phase0/research_cointegration_pairs.md`
- `docs/proposals/phase0/research_london_breakout_adaptive.md`
- `docs/proposals/phase0/research_meta_labeling_ensemble.md`

### 計画・フレーム
- `docs/PHASE_2_PLAN.md` — Phase 2 必須要件 (PF/Sharpe/OOS/Black Swan ゲート)
- `docs/proposals/REVIEW_SUMMARY.md` — Phase 1 集計 (案A/B/C)
- `docs/RETREAT_2026-05-26.md` — SPEC v2 PoC 撤退記録 (effort heuristic 教訓)
- `docs/CYCLE2_PLAN.md` — 第2サイクル「signal_v2 + LLM 補完」計画
- `docs/PROPOSAL_TEMPLATE.md` — 採点フレーム (Phase 3 でフレーム改訂予定)

### memory 教訓 (本サイクルで新規追加)
- `feedback_self_rating_predictive_failure.md`
- `feedback_self_improvement_signal_suppression_trap.md`
- `feedback_statistical_significance_not_economic.md`
- `feedback_phase0_bt_grid_unreliable.md`

---

**作成**: 集計エージェント (Phase 2 第1サイクル 正式記録)
**確認**: ユーザー判断 → 第2サイクル移行決定済 (CYCLE2_PLAN.md)
