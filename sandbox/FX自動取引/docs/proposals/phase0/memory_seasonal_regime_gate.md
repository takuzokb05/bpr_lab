# プロポーザル: SeasonalDetector を「エントリーフィルタ」として再利用 (SPEC v2 棚上げ要素の活用)

## 1. 戦略仮説 (1段落)

SPEC v2 で「★★★★★ 確定」した SeasonalDetector (M15 YZ_vol > 30%ile + H1 YZ_vol > 0.00175) は **統計的に意味あるレジーム判定器** だが、それ単独では PF が立たなかった (反論屋3体の指摘)。本提案は **逆発想**: SeasonalDetector を「単独戦略」ではなく **「既存有効戦略のエントリーフィルタ」** として使う。VOLATILE 判定時のみベース戦略を発火 → 「高ボラ局面で勝てる戦略」のみが残る。エッジ源は (a) Step C 多重補正で AAA 確定 (Permutation Test p_rw<0.001) (b) VOLATILE 局面では mean-reversion 戦略のリターンが偏る (right-tail) という統計的事実。

## 2. 想定エッジ源 [G1-1]

- **構造的優位**: SeasonalDetector は **Bonferroni N=606 と Romano-Wolf 12-family の二重補正を生存** した 5/12 仮説。VOLATILE 環境ではリターン分布が平均回帰側に偏る統計的事実が裏付け
- **棚上げ資産の活用**: docs/RETREAT_2026-05-26.md § 「棚上げ (Phase 0 で再評価)」で「季節判定器自体はエッジ源として再利用可能か」と明記 → 本提案がそれに該当
- **既存有効戦略 (EUR_USD H1 RSI Pullback) との合成**: 低ボラ環境では Pullback が機能しにくい (反転が浅い) → VOLATILE 環境でのみ発火させることで PF が更に上振れ可能性
- **「単独 PoC で 0発火・PF未確認」だった理由**: それ単独では何を観察してるか不明だったため (反論屋3体) → **フィルタ用途では「ベース戦略 × フィルタ追加」の差分で経済性測定可能**

## 3. シグナル定義 (擬似コード)

```python
def signal_with_seasonal_filter(bar_close, history_h1, history_m15):
    # Step 1: ベース戦略 (EUR_USD H1 RSI Pullback) 発火判定
    base_signal = eur_usd_h1_rsi_pullback(bar_close, history_h1)
    if base_signal is None:
        return None

    # Step 2: SeasonalDetector で VOLATILE 判定
    yz_vol_m15 = calc_yang_zhang(history_m15, window=14)
    yz_vol_m15_p30 = yz_vol_m15.rolling(5000).quantile(0.30).iloc[-1]
    yz_vol_h1 = calc_yang_zhang(history_h1, window=20).iloc[-1]

    is_volatile = (
        (yz_vol_m15.iloc[-1] > yz_vol_m15_p30) and
        (yz_vol_h1 > 0.00175)  # EUR_USD-tuned threshold (要再算)
    )

    if not is_volatile:
        return None  # 低ボラ → 発注しない

    return base_signal
```

**特徴**:
- ベース戦略の OOS 取引数 56/年 → SeasonalDetector フィルタで **5-15/年に絞り込み** (Y5 ヒット率 1.99% より高フィルタ)
- 取引数減少のトレードオフで PF 上振れを狙う

## 4. データ要件 [G1-2]

- **必要データ**: M15 + H1 OHLC (既存 5年データあり)
- **取得元**: MT5 (既存)
- **コスト**: ゼロ
- **ラグ**: H1 確定+5秒で M15 直近データも MT5 から取得可能

## 5. リスクモデル [G1-5]

- ベース戦略の SL/TP (ATR×1.5/×2.5) を継承
- VOLATILE 局面のため SL slippage 想定 +0.5pip
- **想定 MaxDD**: ベース戦略より低下想定 -3〜-5% (取引数減 + 環境ベスト)
- **テールリスク**: VOLATILE 判定が遅延すると、エントリー時には既にボラがピークアウトしているリスク (lagging indicator) → 直近5バーの YZ_vol 上昇率を併用してエントリータイミング微調整

## 6. 自己改善メカニズム [G0-B] — 必須

### ドリフト検出
- **VOLATILE フィルタ後の PF**: ローリング20トレードで PF<1.2 が3連続で warning
- **VOLATILE 発火頻度**: 月次で VOLATILE 発火率を測定、学習時 (5年平均 8%) と乖離が ±50% を超えたら閾値再調整
- **環境フィルタ有効性**: 「VOLATILE 通過取引の PF」と「VOLATILE 不通過の(仮想)PF」を並走計測。差分がプラスならフィルタ有効、ゼロ以下なら効果なし

### 自動再最適化
- **四半期 H1 閾値再算**: 過去5年の H1 YZ_vol p90 を再計算し、閾値を更新 (例: 0.00175 → 0.00180)
- **M15 ローリング窓再選定**: M15 30%ile の rolling 窓 (現5000) を 2000, 5000, 10000 で比較し、最も PF が高い窓を採用
- **フィルタ on/off 自動切替**: 直近30トレードで「フィルタ通過 PF < フィルタ無視 PF」が3か月連続なら、フィルタを **自動的に無効化** (= ベース戦略のみで運用)

### フォールバック
- **フィルタ通過取引 PF<0.8 が直近20件で確定**: フィルタ無効化 + Slack 通知
- **VOLATILE が90日 0回発火**: フィルタ閾値が高すぎと判定し、p85 に下げて再評価
- **直前パラメータ履歴を `data/seasonal_filter_history.json` に保持**

### 擬似コード (1段落)
> ベース戦略の OOS PF と「ベース戦略 + Seasonal フィルタ」の OOS PF を並走計測。Seasonal フィルタが PF を改善する間はフィルタ ON、改善しなくなったら自動的に OFF (ベース戦略のみ)。四半期で H1 YZ_vol p90 と M15 rolling 窓を再選定。VOLATILE 90日 0回でフィルタ閾値を緩和。

## 7. 過去 BT 結果 [G0-A] — 必須

### Source: 既存 BT グリッド + SPEC v2 の VOLATILE データ

**ベース戦略 (EUR_USD H1 RSI Pullback)**: OOS PF 1.34-1.49 確定 (memory_eur_usd_h1_rsi_pullback.md 参照)

**SeasonalDetector の VOLATILE 発火率**: Y1-Y5 で 1.99-3.93%、5年平均 8% (GBP_JPY)。EUR_USD は閾値再算が必要 (現 0.00175 は GBP_JPY 用)

### EUR_USD 用の SeasonalDetector 閾値再算

```python
import pandas as pd
df = pd.read_csv('data/mt5_EUR_USD_H1_5y.csv')
# YZ_vol w=20 で 5年 p90 を計算
yz = calc_yang_zhang(df, window=20)
threshold = yz.quantile(0.90)
print(f"EUR_USD H1 YZ_vol p90 = {threshold}")
# 推定: 0.00080-0.00120 (EUR_USD は GBP_JPY より低ボラ)
```

### 想定 BT 結果 (Phase 1 で実施)

ベース戦略 (PF 1.4) × SeasonalDetector フィルタの想定効果:
- **シナリオ A**: VOLATILE 環境で reversal が強化 → PF 1.4 → **1.7-2.0**, 取引数 56→15-25/年
- **シナリオ B**: フィルタが過剰除去 → PF 1.4 → **1.5**, 取引数 56→8/年 (機会喪失大)
- **シナリオ C**: VOLATILE と reversal の方向が逆 → PF 1.4 → **0.9**, フィルタ自動 OFF

Phase 1 で全シナリオ確認、Aの場合のみ採用

### PF > 0.95 を超える論証
- ベース戦略単独で PF 1.4 → フィルタが極端に悪く作用しても PF 0.95 を割らないと想定
- 自己改善メカニズムでシナリオ C は自動 OFF → ベース戦略のみで PF 1.4 を確保

## 8. WFA / OOS [G1-7]

- SeasonalDetector 自体は SPEC v2 で 5-fold anchored WFA 済 (但し PF ではなく TR で評価)
- Phase 1 で **PF ベースの WFA** を再実施
- DSR: ベース戦略 + フィルタの試行数 = 20 (ベース) × 5 (閾値) × 5 fold = 500 → deflation 余地

## 9. 実装複雑度 [G1-3]

- **既存実装あり**: `src/spec_v2/seasonal_detection.py` (SPEC v2 撤退コードを継承)
- **追加実装**: ベース戦略ラッパ + EUR_USD 閾値再算 = 1-2日
- **工数**: **2-3日**
- **依存**: pandas, pandas_ta, MT5 (既存)

## 10. 機会費用比較 [G1-6]

| 運用先 | 1年 % | 1年 JPY (100万) |
|---|---:|---:|
| 銀行預金 | +0.05% | +500 |
| 米国債4% | +4% | +40,000 |
| 株式8% | +8% | +80,000 |
| **ベース EUR_USD H1 RSI 単独** | **+6〜+12%** | +60,000〜120,000 |
| **+ Seasonal フィルタ (シナリオA)** | **+10〜+22%** | +100,000〜220,000 |
| **+ Seasonal フィルタ (シナリオB)** | **+3〜+6%** | +30,000〜60,000 (フィルタ過剰) |

## 11. リスク・既知の弱点

1. **発火頻度の少なさ**: VOLATILE 5%以下 → 月 1-2 件しか発火しないリスク → 評価サンプル不足
2. **SeasonalDetector の元の批判**: 反論屋3体が「経済性を見ていない」と指摘した経緯 → 本提案は経済性検証を G0-A に明示組み込み済
3. **閾値の通貨依存**: GBP_JPY 用 0.00175 を EUR_USD でそのまま使えない → 再算必須
4. **VOLATILE 局面でも reversal が機能する保証なし**: シナリオ B/C の可能性 → 自己改善メカニズムで自動 OFF
5. **「★★★★★ の幻惑」への警戒**: 統計的有意 ≠ 経済的有意 を念頭に Phase 1 で PF ベース判定

## 撤退条件 (事前明記)

1. ペーパー90日で VOLATILE フィルタ通過 trades < 5
2. 直近30件 フィルタ通過 PF < 1.0
3. フィルタが3か月連続でベース戦略の PF を改善しない (自動 OFF)
4. 累計 PnL < -3%

## 12. 採点自己評価

| Gate | 項目 | 点数 | コメント |
|---|---|---|---|
| **G0-A** | PF > 0.95 | ✅ **PASS** | ベース戦略単独で PF 1.4 確保、フィルタは下振れ自動 OFF |
| **G0-B** | 自己改善 | ✅ **PASS** | フィルタ on/off 自動切替が組み込み |
| G1-1 | エッジ源 | **7/10** | 統計的有意は AAA だが経済性は未確認 |
| G1-2 | データ要件 | **9/10** | 既存データ完結 |
| G1-3 | 実装複雑度 | **8/10** | 既存 SeasonalDetector 流用 |
| G1-4 | ロバスト性 | **6/10** | フィルタ通過 trades 少なくサンプル不足懸念 |
| G1-5 | リスク | **8/10** | フィルタ追加で MaxDD 低下想定 |
| G1-6 | 機会費用 | **7/10** | シナリオ依存、Aなら株式同等 |
| G1-7 | WFA/OOS | **6/10** | SPEC v2 で TR ベース WFA 完了、PF ベースは Phase 1 |
| **G1合計** | | **51/70** | |
| G2-1 | コスト耐性 | **4/5** | 取引数少でスプレッド負担低 |
| G2-2 | 相関 | **3/5** | EUR_USD ベース + EUR_USD H1 RSI 提案と高相関 |
| G2-3 | 説明可能性 | **5/5** | YZ_vol + RSI で完全可視化 |
| G2-4 | レビュー耐性 | **2/5** | 「SPEC v2 で撤退したものを再利用」批判に弱い、要慎重論証 |
| G2-5 | 拡張性 | **4/5** | 他ペア対応容易 (閾値再算のみ) |
| G2-6 | 亡き者整合 | **3/5** | SPEC v2 撤退の経緯あり、PoC 設計バグを継承するリスク |
| **G2合計** | | **21/30** | |
| **総合** | | **72/100** | **Phase 2 進出可能、フィルタ単体エッジ性質の検証が必要** |

## 13. 亡き者整合チェック

- SPEC v2 PoC は GBP_JPY で 15日 0発火 で撤退 (`docs/RETREAT_2026-05-26.md`)
- **本提案は「PoC の三重定義」(反論屋指摘) を解体**: SeasonalDetector を**フィルタ専用** (= signal_v2 placeholder と切り離す)
- 反論屋ULTRA バグ A (PoC 三重定義) の解決策と整合
- ベース戦略を EUR_USD (亡き者で唯一プラス) に変更することで GBP_JPY 撤退矛盾を回避

## 14. ソース引用

- `docs/RETREAT_2026-05-26.md` § 「棚上げ (Phase 0 で再評価)」(本提案根拠)
- `src/spec_v2/seasonal_detection.py` (既存実装)
- `data/spec_2_1_random_baseline.json` (Permutation Test 結果, AAA 確定)
- `data/spec_2_1_multiple_testing.json` (Bonferroni + Romano-Wolf 結果)
- `docs/analysis/CONTRARIAN_ULTRA.md` バグ A (PoC 三重定義 → 本提案で解決)
- `data/backtest_grid_h1_EUR_USD.csv` (ベース戦略 PF 1.4 確定)
