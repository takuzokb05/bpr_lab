# Phase 2 BT レポート: #15 Meta-Labeling Ensemble (Lopez de Prado)

**作成日**: 2026-05-26
**担当**: analyst (Phase 2 BT エージェント phase2-bt-15)
**スクリプト**: `scripts/_phase2_bt_15_meta_labeling.py`
**データ**: EUR/USD H1 5年 (主) + USD/JPY H1 5年 (副)、`data/mt5_*_H1_5y.csv`
**所要時間**: 約12分 (RF 学習 + WFA 30 windows × 2 ペア)

---

## 0. TL;DR

| 指標 | 結果 | ゲート | 判定 |
|---|---|---|---|
| **PF (ALL, スプレッド込み)** | **0.79** | ≥1.3 | **FAIL** |
| PF (EUR_USD のみ) | 0.36 | — | 大破綻 |
| PF (USD_JPY のみ) | 1.08 | — | break-even 圏内 |
| **Sharpe (ALL, 年率)** | **-0.89** | ≥0.8 | **FAIL** |
| **OOS trades** | **203** | ≥30 | PASS |
| **機会費用 (米国債 4%)** | **-12,940 JPY (5年累計)** | 預金以上 | **FAIL** |
| Deflated Sharpe | 0.0 | ≥0.5 加点 | FAIL |
| RF OOS AUC (平均) | EUR: 0.504 / UJ: 0.485 | ≥0.55 想定 | **FAIL (ランダム以下)** |
| Black Swan キルスイッチ動作 | データ範囲内事象=0件発生 (期間2021-2026に該当事象 trade 0) | — | 検証未達 |
| Safe Mode 発火 | 2,673回 (Primary 3,818回 中 70%) | — | 過剰棄却 |

**総合判定: Phase 3 進出 非推奨 (廃案または再起草)**

---

## 1. 戦略概要 (Phase 0 からの確定)

### 1.1 Primary 戦略の選定 (meta 委員「対立大 #3」条件解消)

`docs/proposals/REVIEW_SUMMARY.md` の meta 委員指摘:

> Primary 候補を明示してから Phase 2 進出。

**確定: Primary = `ma_crossover` (オプション A)**

選定理由:
1. 指示書 (analyst 起動時の prompt) で「ma_crossover を Primary とする」が推奨されていた
2. MTFPullback は亡き者 PF 0.80 の主因 → Primary に据えると signal_v2 と同じ「未確定戦略を底に積む」構造 (撤退バグ④ 三重定義の再演)
3. ma_crossover は LOOKBACK=5 で確定的にシグナル発生 → Triple-Barrier ラベル付け対象が明確
4. Lopez de Prado 教科書例 (SMA cross) と等価。Primary を単純化することで「Secondary が亡き者の負けパターンを排除できるか」という真の検証問いに集中できる
5. MTFPullback は MTF (M15+H1+H4) なのでラベル品質が複雑化、本BTで検証する責任配分が曖昧になる

### 1.2 戦略仕様 (擬似コード)

```python
# Primary (亡き者 src/strategy/ma_crossover.py の簡素再実装)
def primary_signal(df):
    ma_short = SMA(close, 20)
    ma_long = SMA(close, 60)
    rsi = RSI(close, 14)
    adx = ADX(high, low, close, 14)
    # 直近5本以内のクロス検出 (LOOKBACK=5)
    if cross_up_recent_5 and ma_short > ma_long and rsi < 70 and adx >= 15:
        return +1  # Long
    if cross_dn_recent_5 and ma_short < ma_long and rsi > 30 and adx >= 15:
        return -1  # Short
    return 0

# Triple-Barrier ラベル (Lopez de Prado)
def triple_barrier(side, entry, atr):
    TP = entry + side * 2.0 * atr   # 2 ATR (利確)
    SL = entry - side * 1.0 * atr   # 1 ATR (損切り、RR = 2)
    max_hold = 24 bars              # 1日 (H1)
    return label (1 if TP hit, 0 otherwise), exit_offset, raw_return

# Secondary (Random Forest)
features = [rsi, adx, atr/price, mfi, vol20_std, sma_gap, sma_gap_abs,
            ret_lag_1..5, hour, dow]   # 14個
clf = RandomForestClassifier(
    n_estimators=200, max_depth=4, min_samples_leaf=20,
    class_weight='balanced', random_state=42)

# Walk-Forward
for window in walk_forward(train=12mo, test=3mo, step=3mo):
    clf.fit(features_train, labels_train)
    proba = clf.predict_proba(features_test)[:, 1]
    # Safe Mode: proba < 0.6 なら見送り
    take = proba >= 0.60
    enter_position(side=primary_side, where=take)
```

### 1.3 ペア / TF / パラメータ

| 項目 | 値 |
|---|---|
| ペア | EUR/USD (主), USD/JPY (副) |
| TF | H1 |
| 期間 | 2021-05-07 〜 2026-05-07 (5年, 30,974 bars/ペア) |
| Lot | 0.01 (1,000 units) |
| Spread | EUR_USD: 1.0pip 往復, USD_JPY: 1.0pip 往復 |
| Slippage | 片道 1pip × 2 (entry + exit) |
| Primary | SMA(20)/SMA(60) cross, RSI<70/>30, ADX>=15, LOOKBACK=5 |
| Triple-Barrier | TP=2×ATR(14), SL=1×ATR(14), max_hold=24h |
| RF | n_est=200, max_depth=4, min_leaf=20, balanced |
| Safe Mode | proba<0.6 で見送り |
| WFA | 12ヶ月学習 / 3ヶ月運用 / step 3ヶ月 → 15 windows × 2ペア = 30 windows |
| Embargo | 24bars (purged k-fold 想定の embargo 期間、本実装では window 境界で自然分離) |

---

## 2. BT 結果 (5年、スプレッド込み)

### 2.1 ペア別

| ペア | trades | wins | losses | 勝率 | PF | Sharpe | Sortino | PnL (JPY) | MaxDD (JPY) | 最大連敗 |
|---|---|---|---|---|---|---|---|---|---|---|
| EUR_USD | 92 | 19 | 73 | **20.7%** | **0.36** | -1.66 | -2.00 | -14,610 | -16,854 | 26 |
| USD_JPY | 111 | 42 | 69 | 37.8% | 1.08 | 0.15 | 0.18 | +1,669 | -7,670 | 14 |
| **ALL** | **203** | **61** | **142** | **30.0%** | **0.79** | **-0.89** | **-1.06** | **-12,940** | **-19,497** | **16** |

**注釈**:
- スプレッド + スリッページ込み (EUR_USD: 1pip+2pip=3pip往復コスト相当 / USD_JPY: 同じ)
- スプレッド除外時の PF は別途要算出 (現状未測定)、ただしコスト除外でも RF AUC<0.5 のため改善見込み薄
- EUR_USD 勝率 20.7% は SMA cross + RSI/ADX フィルタ + Secondary の上位 6.25% 採用 後の値 → **Secondary が選んだ取引でも 79.3% が負け** = Secondary 完全失敗

### 2.2 Deflated Sharpe Ratio

- 観測 Sharpe = -0.89 (負値)
- 試行数推定 (WFA windows × ペア × parameter trial 5) = 150
- DSR = **0.00** (期待最大 SR を全く超えていない)

### 2.3 Primary / Secondary の役割明示 (指示書「重要要件」)

| 指標 | EUR_USD | USD_JPY |
|---|---|---|
| Primary 全イベント (5年) | 1,958 | 1,860 |
| Test 期間 Primary 発火数 (合計) | 1,472 | 1,404 |
| Secondary が「取る」と判定 (proba≥0.6) | 92 | 111 |
| **採用率 M/N** | **6.25%** | **7.91%** |
| Safe Mode 発火 (proba<0.6) | 1,380 | 1,293 |
| RF OOS AUC (15 window 平均) | 0.504 | 0.485 |
| RF OOS Accuracy (15 window 平均) | ~0.61 | ~0.65 |

**重大な観察**:
- **RF OOS AUC ≒ 0.5 = ランダム以下**。Secondary は実質的に Primary シグナルを区別できていない
- それなのに採用率 6-8% と極端に低い ≒ class_weight='balanced' で「取らない方が安全」側に学習された
- 採用したわずかな取引も勝率 EUR 20.7% / UJ 37.8% で、Primary 単独 (理論的勝率 ~40%) より EUR では悪化

→ **「敗者を排除する」設計が機能せず、むしろ Primary より悪い取引だけを採用した**

---

## 3. Walk-Forward Analysis (15 windows × 2 ペア = 30 windows)

### 3.1 EUR_USD WFA (15 windows)

| Test 開始 | Primary 発火 | Secondary 採用 | RF AUC | PF | Sharpe | trades | PnL |
|---|---|---|---|---|---|---|---|
| 2022-05-07 | 103 | 19 | 0.448 | 0.19 | -3.49 | 19 | -5,262 |
| 2022-08-07 | 98 | 12 | 0.562 | 0.17 | -2.40 | 12 | -2,756 |
| 2022-11-07 | 97 | 6 | 0.497 | 0.31 | -8.28 | 6 | -1,116 |
| 2023-02-07 | 110 | 11 | 0.319 | 0.41 | -1.27 | 11 | -1,352 |
| 2023-05-07 | 81 | 0 | 0.519 | — | — | 0 | 0 |
| 2023-08-07 | 98 | 6 | 0.479 | 0 | 0 | 6 | -1,328 |
| 2023-11-07 | 126 | 5 | 0.511 | 0.33 | -4.48 | 5 | -647 |
| 2024-02-07 | 87 | 4 | 0.383 | 0.44 | 0 | 4 | -421 |
| 2024-05-07 | 106 | 1 | 0.433 | 0 | 0 | 1 | -274 |
| 2024-08-07 | 126 | 3 | 0.616 | ∞ (3勝0敗) | 0 | 3 | +1,418 |
| 2024-11-07 | 92 | 8 | 0.449 | 0.49 | -1.59 | 8 | -946 |
| 2025-02-07 | 84 | 8 | 0.419 | 0 | -3.96 | 8 | -3,290 |
| 2025-05-07 | 98 | 1 | 0.525 | 0 | 0 | 1 | -303 |
| 2025-08-07 | 93 | 1 | 0.660 | 0 | 0 | 1 | +525 |
| 2025-11-07 | 73 | 7 | 0.741 | **3.46** | 1.78 | 7 | +1,142 |

### 3.2 USD_JPY WFA (15 windows)

| Test 開始 | Primary 発火 | Secondary 採用 | RF AUC | PF | Sharpe | trades | PnL |
|---|---|---|---|---|---|---|---|
| 2022-05-07 | 91 | 6 | 0.518 | **2.26** | 5.79 | 6 | +674 |
| 2022-08-07 | 81 | 18 | 0.637 | 1.02 | 0.06 | 18 | +78 |
| 2022-11-07 | 90 | 16 | 0.342 | 0.40 | -1.25 | 16 | -2,549 |
| 2023-02-07 | 101 | 8 | 0.582 | 0.56 | -6.49 | 8 | -778 |
| 2023-05-07 | 74 | 6 | 0.691 | 0.81 | -1.03 | 6 | -208 |
| 2023-08-07 | 94 | 0 | 0.400 | — | — | 0 | 0 |
| 2023-11-07 | 95 | 0 | 0.505 | — | — | 0 | 0 |
| 2024-02-07 | 119 | 1 | 0.351 | 0 | 0 | 1 | -217 |
| 2024-05-07 | 97 | 6 | 0.372 | 0 | -5.80 | 6 | -1,714 |
| 2024-08-07 | 98 | 0 | 0.548 | — | — | 0 | 0 |
| 2024-11-07 | 83 | 1 | 0.507 | 0 | 0 | 1 | -419 |
| 2025-02-07 | 100 | 29 | 0.484 | **1.74** | 1.58 | 29 | +4,397 |
| 2025-05-07 | 102 | 9 | 0.582 | **3.82** | 3.54 | 9 | +2,139 |
| 2025-08-07 | 100 | 11 | 0.441 | 1.17 | 0.36 | 11 | +267 |
| 2025-11-07 | 79 | 0 | 0.314 | — | — | 0 | 0 |

### 3.3 安定性評価

- **PF >= 1.3 をクリアした windows: 5/30 (16.7%)**
- うち trades>=10 は 2/30 (USD_JPY 2025-02 / 2022-08)
- 残り 25 windows は PF < 1.3 もしくは trades<3 で統計的有意性なし
- **EUR_USD 最近4窓 (2024-11以降) で 4回中 3回がほぼ取引なし or 大敗**
- 「2025-11 EUR_USD で PF 3.46」「2025-05 USD_JPY で PF 3.82」のような数字は **trades 7-9 で偶然性が高い**
- WFA 全体の Sharpe = -0.89 が「窓ごとの偶発的成功」が全体損失を埋め合わせできていないことを示す

---

## 4. パラメータ感度 (Safe Mode 閾値)

| 閾値 | trades | PF | PnL (JPY) | 評価 |
|---|---|---|---|---|
| 0.48 (-20%) | 203 | 0.79 | -12,940 | 大敗 |
| 0.54 (-10%) | 203 | 0.79 | -12,940 | 大敗 |
| **0.60 (基準)** | **203** | **0.79** | **-12,940** | **基準** |
| 0.66 (+10%) | 32 | 1.31 | +1,406 | PF 1.31 だが OOS<30 |
| 0.72 (+20%) | 7 | 4.17 | +2,844 | trades=7、過剰適合の典型 |

**観察**:
- 閾値 -20% 〜 基準まで PF は変動なし (本実装で proba<0.6 は既に切られているため、低い閾値の sensitivity は事実上同じ)
- 閾値 +10% で trades が 32 に激減し PF が 1.31 に上昇 → これは **「閾値を引き上げて trades を減らす」というアドホックな特殊化**であり、Phase 0 申請の「6%」設計とは異なる
- 閾値 +20% で PF 4.17 だが trades 7 → 完全に統計的根拠なし

→ **「閾値を上げて勝つ」は過剰適合と区別できない**。Phase 2 進出基準の「±20% で PF が 0.8x 以下に落ちない」を「悪化方向」で評価すれば PASS だが、「改善方向」の解釈なら過剰適合警告。

---

## 5. Black Swan ストレステスト

**5事象 (2015 SNB / 2016 Brexit / 2020 COVID / 2024 円介入×2 / 2024 carry unwind) すべて**:

| 事象 | 期間 | EUR/USD trades | USD/JPY trades | 結果 |
|---|---|---|---|---|
| 2015 SNB | 2015-01-12〜20 | 0 | 0 | **データ範囲外** (2021-から) |
| 2016 Brexit | 2016-06-22〜27 | 0 | 0 | **データ範囲外** |
| 2020 COVID | 2020-03-09〜23 | 0 | 0 | **データ範囲外** |
| 2024 JPY介入 07 | 2024-07-10〜15 | 0 | 0 | 取引なし (Safe Mode で全棄却) |
| 2024 JPY介入 08 | 2024-08-01〜08 | 0 | 0 | 取引なし (Safe Mode で全棄却) |
| 2024 carry unwind | 2024-08-02〜06 | 0 | 0 | 取引なし (同上) |

**結論**:
- データ範囲 (2021-05〜2026-05) 制約で 2015/2016/2020 事象は **検証不能**
- 2024 円関連事象は **Secondary が「全イベントを棄却」した** → 結果的に損失回避できたが、これは「キルスイッチが正常動作した」のではなく「常時 Safe Mode で過剰棄却している副作用」
- **真のキルスイッチ機構 (VIX>30、1日±3σ、スプレッド3倍) は本BTで未実装** → Phase 3 進出に必須の検証項目が達成できていない
- 8/5 のクロス円大幅下落で USD/JPY 2024-08 window (test_start 2024-08-07) では Secondary が 0件採用 → **データを見て学習した結果として「危険な時期だ」と察知できた可能性はある** が、AUC 0.548 ではエビデンス薄

---

## 6. リスク管理シミュレーション

| 項目 | 発動回数 (5年, ALL) |
|---|---|
| 日次 -1.5% (-15,000 JPY) 警告 | 0 |
| 日次 -3% (-30,000 JPY) 半量化 | 0 |
| 日次 -5% (-50,000 JPY) 停止 | 0 |
| 月次 -10% (-100,000 JPY) 月停止 | 0 |

**観察**:
- そもそも 1取引の損失が約 30-300 JPY (lot 0.01) のため、日次 -1.5% (15,000 JPY) を超える日が物理的に発生不能
- 想定 MaxDD (Phase 0 申請 = 8-15%) に対し実測 MaxDD = -19,497 JPY (約 -1.95% / 初期資金100万円)
- リスク管理基準は **「発動しないので動作確認できない」**

→ **Lot を 0.01 → 0.1 (10倍) に上げた場合の挙動が Phase 3 進出には必要**。本BTでは「想定通り低リスク」だが「PnL も低リスクで小さすぎる」=機会費用負け。

---

## 7. 自己改善メカニズム動作 (G0-B 実証)

### 7.1 Secondary Model 月次再学習

- **実装方式**: Walk-Forward (3ヶ月step) で疑似再学習を実現
- **発動回数**: EUR_USD 15回 / USD_JPY 15回 = 計 **30回**
- **AUC 推移**: 0.319 (2023-02) 〜 0.741 (2025-11) と大きく揺れる
- **判定**: 「再学習は機能しているが、再学習しても AUC が ~0.5 (ランダム) を抜けない」 = **メカニズムは動くがエッジを学習できていない**

### 7.2 Safe Mode (proba<0.6) フォールバック

- 発動回数: **2,673回** (5年, 両ペア合計)
- Primary 発火 3,818回のうち **70.0% を棄却**
- 残り 30% に絞っても全体 PF 0.79 → **フォールバックは過剰反応で機会喪失**

### 7.3 ロールバック (OOS AUC が直前比 -10% 低下時)

- 本BTでは未実装 (簡素化のため)
- Phase 3 進出時の実装課題

### 7.4 撤退条件シミュレーション

| 撤退条件 | 発生回数 (lot 0.01 換算) |
|---|---|
| 90日 trades<5 | EUR_USD で **頻発** (15 window のうち 0件/1件/3件/4件が 8回) |
| PF<1.0 (累計) | 全期間で 5年累計 PF=0.79、開始時点から該当 |
| 累計 -3,000 JPY | 約2年目で到達 (EUR_USD), 4年目 (ALL) |

**結論**: **撤退条件をシミュレートすると、2年以内に複数回 trigger される** → 実取引投入なら 1年以内に撤退判断必須。Phase 0 申請の「自己改善メカニズム」は機能しているが、**「機能した結果として撤退すべき」と教えてくれる**自己改善である。

---

## 8. 機会費用比較

| 対象 | 想定年率 | 100万円運用 × 5年 | 評価 |
|---|---|---|---|
| 銀行預金 (0.05%) | +0.05% | **+2,500 JPY** | 預金以下 |
| 米国債 (4%) | +4% | **+216,000 JPY** | 大幅劣後 |
| 全世界株 (8%) | +8% | **+469,000 JPY** | 大幅劣後 |
| **本戦略 (実測)** | **-0.26%/年** | **-12,940 JPY** | **マイナスリターン** |

→ **預金以下 = 機会費用負け**。Phase 0 申請の「12-20%/年」は **大幅未達** (実測 -0.26%/年)。

---

## 9. ゲート判定

### 9.1 必須条件

| ゲート項目 | 結果 | 判定 |
|---|---|---|
| PF ≥ 1.3 | 0.79 | **FAIL** |
| Sharpe ≥ 0.8 | -0.89 | **FAIL** |
| OOS trades ≥ 30 | 203 | PASS |
| 機会費用 (米国債 4%) 超過 | -12,940 < +216,000 | **FAIL** |
| 日次/月次損失上限 実装+作動確認 | 実装済、未発動 (lot小すぎ) | **要再検証** |
| Black Swan キルスイッチ作動 | データ範囲外 + 該当事象0 | **FAIL (検証未達)** |
| 自己改善メカニズム実証 | WFA再学習 30回、Safe Mode 過剰、撤退条件 trigger | **動作するが効果なし** |

### 9.2 加点項目

| 項目 | 結果 | 判定 |
|---|---|---|
| Sortino ≥ 1.0 | -1.06 | FAIL |
| Deflated Sharpe ≥ 0.5 | 0.00 | FAIL |
| MaxDD ≤ 15% | -1.95% (= 低リスクだが PnL も小) | パス (ただし lot 小) |
| パラメータ感度 ±20% で PF 0.8x | 悪化方向 OK / 改善方向は過剰適合 | 部分 PASS |
| WFA 6 windows 中 4 以上 PASS | 30 windows 中 PF≥1.3 = 5 (16.7%) | **FAIL** |

### 9.3 総合判定

**Phase 3 進出 非推奨 / 廃案または再起草 (Primary を MTFPullback に差し替えた再検証は別工数で可)**

判定根拠:
1. PF 0.79 < ゲート 1.3 — 50% 不足
2. Sharpe -0.89 — ゼロ未満、機会費用 (米国債) 大幅劣後
3. RF OOS AUC 0.49 = **ランダムフォレストがランダム以下** = Secondary が機能していない決定的証拠
4. WFA 30 windows のうち PF≥1.3 をクリアしたのは 5 windows (16.7%) — 安定性なし
5. Safe Mode が Primary 発火の 70% を棄却するも、残り 30% は Primary 単独より悪い

---

## 10. 分析 — なぜ機能しなかったか (正直な振り返り)

### 10.1 「Phase 0 では美しい設計だったが、実装したら効かなかった」(指示書注意事項)

**Phase 0 申請** (`research_meta_labeling_ensemble.md`) の主張:
- Lopez de Prado 原典で Sharpe 0.5 → 1.2 改善
- Hudson & Thames で Sharpe 1.4 → 2.0
- 「Primary が PF 0.8 でも、Secondary が False Positive 半減すれば PF 1.4 以上に」

**実測結果**:
- Primary 単独の理論 PF を測定していないので比較不能だが、Secondary 採用後の PF が 0.79
- RF OOS AUC = 0.49 (EUR) / 0.48 (UJ) = **Secondary はラベルを予測できていない**
- 「False Positive 半減」は実現せず、むしろ「True Positive まで切り捨てる」結果に (採用率 6-8%、勝率は採用後も 20.7%/37.8%)

### 10.2 構造的な失敗要因

1. **特徴量の問題**:
   - RSI / ADX / ATR / MFI / SMA gap / 直近5本リターン / 時間 — どれも「過去の価格情報」しかない
   - **将来の TP/SL 到達確率に対する真の情報源がない**
   - 「敗者を選別する」には**現在のレジーム** (例: トレンド継続 vs レンジ転換) を特徴量に入れる必要があったが、本BTでは入れていない

2. **Primary 自体が弱い**:
   - ma_crossover は LOOKBACK=5 で多数のシグナルを出すが、その多くが偽 (5年で 1,958 + 1,860 = 3,818件 = 月平均64件)
   - **Primary がランダム以下なら Secondary も救えない** (QuantConnect の "Not a Silver Bullet" 警告そのもの)
   - 亡き者 ma_crossover の本番 PF は別途要確認 (該当データは `fx_trading.db` 内、本BT外)

3. **Triple-Barrier のラベル品質**:
   - TP=2×ATR, SL=1×ATR (RR=2) で max_hold=24h
   - 多くの場合「max_hold 24h で時間切れ」になり、ラベルが「ノイズ」化
   - **ラベル分布が偏らないこと自体は良いが、Secondary が学習する「成功条件」が明確でない**

4. **Safe Mode 閾値 0.6 の妥当性**:
   - balanced class_weight で学習した結果、predict_proba の分布が 0.4〜0.6 に集中
   - 閾値 0.6 で 70% 棄却 → 残った 30% も「proba ちょうど 0.6 付近」=情報量低い
   - 閾値を 0.66 に上げると trades 激減 (32件) で PF 1.31 になるが、サンプル不足で信頼不能

### 10.3 撤退教訓 (`RETREAT_2026-05-26.md`) との関係

亡き者撤退の構造バグ① 「検証範囲と運用範囲のミスマッチ」を本BTでは回避できた:
- Primary + Secondary + 実トレード をすべて同じパイプラインで検証
- スプレッド込みの実 PF を測定
- OOS trades 203 件で統計的根拠は最低限確保

しかし新しいバグも露呈:
- **「美しい設計が機能しなかった」を正直に書く必要がある** = Phase 0 申請の自己採点 85/100 は実測 PF 0.79 と整合しない
- Phase 0 採点フレームが Goodhart 化していた meta 委員指摘の正しさが、本BT で実証された

---

## 11. 自己反論セクション (反論屋応答想定)

### Q1. 「閾値 0.72 で PF 4.17 だ。これを Phase 3 で使えば良いのでは?」
- A: trades=7 件はサンプル不足。Deflated Sharpe で deflate すれば有意性消失。**過剰適合の典型**で、SPEC v2 撤退時の Pragmatist 警告 (PF 0.95 の signal_v2) と同じ罠

### Q2. 「USD/JPY だけなら PF 1.08 で break-even。USD/JPY に絞れば?」
- A: 5年 PnL +1,669 円 = 年率 333 円/100万円 = **0.033%/年**。預金 0.05% 以下。**機会費用負け**

### Q3. 「RF のハイパラを Optuna で最適化すれば?」
- A: 申請書通り。ただし本BTで max_depth/min_leaf は保守的に設定済 (Phase 0 申請の n_est=200 等を踏襲)。**ハイパラ最適化で AUC 0.5 → 0.6 を実現できる根拠がない** (特徴量に情報がない限り)

### Q4. 「Primary を MTFPullback に変えれば?」
- A: 可能性はある。ただし MTFPullback は亡き者 PF 0.80 で本番敗北の主因 = **「meta-labeling を MTFPullback に適用したら劇的に PF 改善」という仮説の検証は別BTが必要**。本BTのスコープ外

### Q5. 「データ範囲を 2015 以前に拡張して Black Swan を検証すれば?」
- A: MT5 から 2015 SNB / 2016 Brexit / 2020 COVID のデータを取得すれば可能。ただし **「ペア通貨の有効性 (PF 0.79)」が解決していない状態で Black Swan 耐性を見ても意味薄**。優先順位は (1) ペア有効性 → (2) Black Swan

---

## 12. 推奨アクション

### 12.1 即時 (本BT 結果として推奨)

1. **本候補は廃案** — Phase 0 自己採点 85/100 と実測 PF 0.79 の乖離が大きすぎる
2. **採点フレーム改訂 (meta 委員の指摘) の正当性をレポートで強化** — Phase 0 申請段階で「美しい設計」が点数を取れる構造は Goodhart 化の証拠

### 12.2 もし再起草するなら (条件付き)

1. **Primary を変える**:
   - MTFPullback (亡き者の負け戦略) を Primary に → meta が「敗者除外できるか」のテスト ← より純粋な仮説検証
   - もしくは Bollinger reversal (亡き者 bollinger_reversal.py)
2. **特徴量を増やす**:
   - レジーム判定 (HMM / YZ_vol) を入力に
   - マルチTF (M15 + H1 + H4) の指標を集約
3. **データ範囲を拡張**:
   - 2015-2020 を含む 10年 D1 → Black Swan 検証必須化
4. **再起草時の自己採点ルール**:
   - PF 1.3 を「実測で示せる根拠」を申請書に書く (文献引用は副材料、自前BTが主)

### 12.3 他候補との関連

- **#1 EUR_USD H1 RSI Pullback** が単独で PF 1.49 を達成しているなら、それを Primary にして meta-labeling を重ねるのが「素直」な次手
- **#12 Cointegration Pairs** が方向中立で機能するなら、meta-labeling より Portfolio 化が高効率
- 本BT結果は **「meta-labeling は銀の弾丸ではない」(QuantConnect)** の実証として、他候補評価の参考材料に

---

## 13. 出力ファイル一覧

| ファイル | 内容 |
|---|---|
| `scripts/_phase2_bt_15_meta_labeling.py` | BT 本体スクリプト |
| `data/_phase2_bt_15_meta_trades.csv` | 全 203 trades 詳細 (entry/exit/proba/PnL) |
| `data/_phase2_bt_15_meta_monthly.csv` | 月次 PnL (ペア × 月) |
| `data/_phase2_bt_15_meta_stress.csv` | Black Swan 5事象 × 2ペア |
| `data/_phase2_bt_15_meta_features.csv` | 特徴量サンプル (EUR_USD 直近1000本) |
| `data/_phase2_bt_15_meta_labels.csv` | Primary シグナル分布 |
| `data/_phase2_bt_15_meta_wfa_eu.csv` | EUR_USD WFA 15 windows 詳細 |
| `data/_phase2_bt_15_meta_wfa_uj.csv` | USD_JPY WFA 15 windows 詳細 |
| `data/_phase2_bt_15_meta_summary.json` | 全サマリ JSON |

---

## 14. 参照

- 候補本体: `docs/proposals/phase0/research_meta_labeling_ensemble.md`
- Phase 2 計画: `docs/PHASE_2_PLAN.md`
- 6評価集計: `docs/proposals/REVIEW_SUMMARY.md`
- 撤退記録: `docs/RETREAT_2026-05-26.md`
- Primary 戦略実装: `src/strategy/ma_crossover.py`
- Lopez de Prado (2018), "Advances in Financial Machine Learning"
- Hudson & Thames, "Does Meta Labeling Add to Signal Efficacy?"
- QuantConnect, "Why Meta-Labeling Is Not a Silver Bullet"
