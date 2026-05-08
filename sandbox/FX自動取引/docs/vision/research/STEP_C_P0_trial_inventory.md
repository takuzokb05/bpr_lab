# Step C P0-1: 試行数 N 棚卸し

> **目的**: SPEC_v2.md § 2-1 の閾値選定で行われた試行（指標 × length × 時間軸 × ペア × 閾値グリッド × 分割）の総数を集計し、Bailey-López de Prado (2014) False Strategy Theorem に基づく **Deflated TR** の計算根拠を整える
> **対象**: `scripts/_spec_2_1_*.py` 系のみ。Phase 1C は戦略改善で別レイヤー、本対象外
> **作成日**: 2026-05-08

---

## スクリプト別 試行空間

### S1. `_spec_2_1_adx_threshold.py`

ADX trending 閾値の Walk-forward 検証 (ADX 単独, M15 短期)

| 軸 | 値 | 数 |
|---|---|---:|
| 指標 | ADX | 1 |
| length | period=14 固定 | 1 |
| 時間軸 | M15 | 1 |
| ペア | USD_JPY, EUR_USD, GBP_JPY | 3 |
| 閾値 | [18, 20, 22, 25, 28, 30, 35] | 7 |
| IS/OOS 分割 | 単一 (75:25) | 1 |
| **小計** | | **21** |

### S2. `_spec_2_1_indicator_screening.py`

6指標スクリーニング（CHOP, Hurst, YZ_vol, Range_ATR, VR, MFI）

| 軸 | 値 | 数 |
|---|---|---:|
| 指標 × 各指標の閾値グリッド | CHOP(6) + Hurst(5) + YZ_vol(4 percentile) + Range_ATR(5) + VR(6) + MFI(5) = 31 | 31 |
| length | 各指標固定 (CHOP=14, Hurst window=100, YZ window=20, Range_ATR period=14, VR q=4, MFI=14) | 1 |
| 時間軸 | M15 / H1 / D1 (3回実行: `spec_2_1_indicator_screening{,_H1_5y,_D1_10y}.json` 確認) | 3 |
| ペア | 3 | 3 |
| IS/OOS 分割 | 単一 | 1 |
| **小計** | | **279** |

### S3. `_spec_2_1_d1_yz_vol_revalidation.py`

YZ_vol 細パーセンタイルグリッドの再検証（D1, M15 で実行確認）

| 軸 | 値 | 数 |
|---|---|---:|
| 指標 | YZ_vol | 1 |
| length | window=20 固定 | 1 |
| 時間軸 | D1, M15 (`spec_2_1_d1_yz_vol_revalidation.json`, `spec_2_1_yz_vol_revalidation_M15_2y.json` の2件確認) | 2 |
| ペア | 3 | 3 |
| 閾値 (percentile) | [30, 40, 50, 55, 60, 65, 70, 75, 80] | 9 |
| IS/OOS 分割 | 単一 | 1 |
| **小計** | | **54** |

### S4. `_spec_2_1_length_sensitivity.py`

YZ_vol window と CHOP length の感度分析

**YZ_vol 部分**:
| 軸 | 値 | 数 |
|---|---|---:|
| 時間軸 | D1, H1, M15 | 3 |
| window | [10, 14, 20, 30] | 4 |
| ペア | 3 | 3 |
| 閾値 | YZ_PERCENTILES = [30, 50, 60, 70, 80] | 5 |
| **小計** | | **180** |

**CHOP 部分**:
| 軸 | 値 | 数 |
|---|---|---:|
| 時間軸 | M15 | 1 |
| length | [7, 10, 14, 21] | 4 |
| ペア | 3 | 3 |
| 閾値 | CHOP_GRID = [30, 35, 38.2, 42, 50, 60] | 6 |
| **小計** | | **72** |

**S4 計**: 180 + 72 = **252**

---

## 全体集計

| スクリプト | 試行数 |
|---|---:|
| S1: ADX threshold | 21 |
| S2: indicator screening (× 3 timeframes) | 279 |
| S3: D1 YZ_vol revalidation (D1+M15) | 54 |
| S4: length sensitivity (YZ + CHOP) | 252 |
| **合計 N** | **606** |

### 注釈

- 重複試行（S2 の YZ_vol M15 と S3, S4 で window=20 の M15 試行が重複しうる）を控除しても **N ≈ 550-600** のオーダー
- 各「試行」は (指標 × length × 時間軸 × ペア × 閾値) の1点を IS/OOS 単一分割で評価したもの
- **不採用となった試行も全部カウント対象**（Bailey 2014 Pseudo-Mathematics 原則 — N は「試したものすべて」、選んだものではない）

---

## Bailey-López de Prado への適用

### 1. False Strategy Theorem

> 真のシャープレシオが全て 0 の N 個の戦略から最大値を選ぶと、その期待値は **`E[max(SR)] ≈ √V × ( (1-γ)·Z⁻¹(1 - 1/N) + γ·Z⁻¹(1 - 1/(N·e)) )`** で膨らむ
> （γ = Euler-Mascheroni 定数 ≈ 0.5772, V = 戦略間 Sharpe 分散）

### 2. TR への類推適用 (近似)

TR は Sharpe 比ではないが、片側中央値の比という意味で類似のスケール変動を持つと仮定し、簡易的に:

```
E[max(TR_observed)] ≈ TR_true + σ_TR × √(2·ln(N))
```

ここで `σ_TR` は TR の bootstrap 標準偏差（未実測 → P0-2 で算出する）。

### 3. 仮計算（σ_TR = 0.15 と仮定した時）

```
E[max(TR)] ≈ 1.0 + 0.15 × √(2 × ln(606))
            = 1.0 + 0.15 × √12.83
            = 1.0 + 0.15 × 3.58
            = 1.0 + 0.537
            ≈ 1.54
```

**含意**: σ_TR=0.15 を仮定すると、**真値 1.0（=ノイズ）でも N=606 試行の最大値は約 1.54 まで膨らむ**。

我々の SPEC_v2.md § 2-1 で採用された TR 値の範囲は **IS_TR 1.08〜2.02 / OOS_TR 1.14〜2.03**。これらのうち deflation 後の信頼度は:

| 採用値の TR 帯 | Deflation 後の解釈 (σ_TR=0.15 仮定) |
|---|---|
| 〜1.5 | **ほぼノイズと区別不可** (D1 EUR_USD OOS_TR=1.21, M15 USD_JPY OOS_TR=1.14, M15 USD_JPY OOS_TR=1.20 等) |
| 1.5〜1.8 | グレーゾーン |
| 1.8〜 | 残る可能性高（H1 USD_JPY OOS_TR=1.92, H1 EUR_USD OOS_TR=1.92, H1 GBP_JPY OOS_TR=2.03） |

### 4. 注意事項

- σ_TR=0.15 は**仮定値**。実測必須 → P0-2 (BCa bootstrap) で求める
- σ_TR が大きいほど deflation も大きくなる → TR 値が信号でなくノイズだった可能性が高まる
- **N=606 は "試した分のみ" の下限**。「同じ計算を別パラメータで走らせた裏のスクリプト」「git に残らない試行錯誤」は含まれない

---

## 結論

1. **試行数 N ≈ 600** は Bailey-López de Prado (2014) の「**5年分日次データなら 7 戦略試すだけで偽陽性が一定確率で出る**」を遥かに超える
2. SPEC_v2.md § 2-1 で採用された TR 値のうち **OOS_TR 1.5 未満の項目はノイズと区別不可の可能性が高い** (σ_TR の仮定次第)
3. 厳密な判定には **σ_TR の実測 (P0-2 BCa bootstrap)** と **Deflated TR 公式の正確な適用** が必要
4. **暫定結論**: 現状の SPEC_v2.md § 2-1 採用閾値は「**Deflation 未補正の名目値**」であり、本番投入前に P0-2 を完遂する必要がある

---

## 該当する SPEC_v2.md § 2-1 採用閾値の deflation 危険度ランキング (σ_TR=0.15 仮定)

| 採用閾値 | OOS_TR | Deflation 後の信頼度 (σ_TR=0.15) |
|---|---:|---|
| **D1 YZ_vol EUR_USD** > 0.00537 | 1.21 | 🔴 高リスク (ノイズと区別困難) |
| **M15 YZ_vol USD_JPY** > 0.00038 (window=14) | 1.14 | 🔴 高リスク |
| **M15 YZ_vol GBP_JPY** > 0.00039 | 1.23 | 🔴 高リスク |
| **M15 CHOP USD_JPY** < 35 | 1.20 | 🔴 高リスク |
| **M15 CHOP EUR_USD** < 30 | 1.21 | 🔴 高リスク |
| **M15 CHOP GBP_JPY** < 30 | 1.26 | 🔴 高リスク |
| **D1 YZ_vol USD_JPY** > 0.00549 | 1.60 | 🟡 グレー |
| **D1 YZ_vol GBP_JPY** > 0.00570 | 1.72 | 🟡 グレー |
| **M15 YZ_vol EUR_USD** > 0.00054 | 1.74 | 🟡 グレー |
| **H1 YZ_vol USD_JPY** > 0.00174 | 1.92 | 🟢 残る可能性 |
| **H1 YZ_vol EUR_USD** > 0.00143 | 1.92 | 🟢 残る可能性 |
| **H1 YZ_vol GBP_JPY** > 0.00175 | 2.03 | 🟢 残る可能性 |

**中期 H1 の YZ_vol だけが Deflation 後も残る可能性が高い**。M15 補完層と D1 長期層の大半は再評価が必要。

---

## 次のステップ (P0-2)

`_spec_2_1_*` 系を改修し、各採用閾値について:

1. **TR を PF (Profit Factor) に置換**: gross profit / gross loss、または条件付き期待値比
2. **BCa bootstrap で 95% CI を計算**: per-bar resampling, 1000+ replicates
3. **Romano-Wolf 多重補正後 p 値**: 閾値スイープを stepwise に処理
4. **Deflated Sharpe Ratio (DSR)** を Bailey 2014 公式で計算: N=606 を入力、σ_TR を実測値に置換

これにより SPEC_v2.md § 2-1 の **★Deflation** 列を実数値で埋められる。
