# プロポーザル: Tick Volume Profile + Value Area 反転

## 1. 戦略仮説

FX は分散型市場で「真の出来高」が不明だが、**MT5 が提供する Tick Volume (ティック数 = 価格変動回数)** は実出来高の代理指標として有効。日次/週次の **Volume Profile** から **POC (Point of Control)**, **Value Area High/Low (VAH/VAL)** を識別し、価格が **VAL/VAH に到達した時の反転**を狙う。Order Flow の完全可視化ができないFXの制約下で、**「フットプリント代用」** として実装可能なアプローチ。

## 2. 想定エッジ源 [G1-1]

- **Volume Profile の支持/抵抗効果**: 過去に多くの取引が成立した価格帯は **「磁石」** として機能 (microstructure 理論)
- **Value Area Edge への反転**: 統計的に **VAH/VAL** で価格反転確率が高い (Steidlmayer 1985 Market Profile)
- **Tick Volume の有効性**: 真の出来高ではないが、**取引アクティビティの代理指標として相関 0.7-0.9** (BIS, mql5 forum 検証)
- **構造的優位**: 大口プレイヤーが POC 周辺で建玉を構築し、VA edge で利確することで支持/抵抗が形成される (microstructure)
- **既知のリスク**: FX の OTC 構造で order book 完全不可視 → ATAS 等の有料ツールでも完璧ではない

## 3. シグナル定義 (擬似コード)

```python
# Stage 1: Volume Profile 計算 (日次, M5 ベース)
def compute_volume_profile(bars_m5, num_bins=50):
    price_range = (bars_m5['low'].min(), bars_m5['high'].max())
    bins = np.linspace(*price_range, num_bins)
    volume_per_bin = np.zeros(num_bins)
    for _, bar in bars_m5.iterrows():
        # 各バーの価格範囲を bins に分散させて tick_volume を累積
        in_range = (bins >= bar['low']) & (bins <= bar['high'])
        volume_per_bin[in_range] += bar['tick_volume'] / sum(in_range)
    return bins, volume_per_bin

# Stage 2: POC, VAH, VAL を特定
poc_idx = volume_per_bin.argmax()  # 最大出来高価格
poc = bins[poc_idx]
# Value Area = total tick_volume の 70% を含む価格帯
sorted_idx = np.argsort(volume_per_bin)[::-1]
cumulative = 0
va_indices = []
for idx in sorted_idx:
    cumulative += volume_per_bin[idx]
    va_indices.append(idx)
    if cumulative >= 0.7 * volume_per_bin.sum():
        break
vah = bins[max(va_indices)]
val = bins[min(va_indices)]

# Stage 3: シグナル (現在価格が VA edge に到達)
current_price = bars_h1['close'].iloc[-1]

if current_price <= val * 1.001:  # VAL タッチ
    if rsi_h1 < 40 and price_velocity_slowing:  # 反転確認
        enter_long(sl=val - 2*atr, tp=poc, size=base_lot)
elif current_price >= vah * 0.999:  # VAH タッチ
    if rsi_h1 > 60 and price_velocity_slowing:
        enter_short(sl=vah + 2*atr, tp=poc, size=base_lot)
```

## 4. データ要件 [G1-2]

- **必要データ**: M5 + H1 OHLCV + tick_volume (MT5 から直接取得可)
- **取得元**: MT5 (`mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, ...)`、`tick_volume` フィールド含む)
- **計算リソース**: 日次 Volume Profile 計算 = 数百 ms
- **ラグ**: バー閉鎖 + < 1秒

## 5. リスクモデル [G1-5]

| 項目 | 設定 |
|---|---|
| ポジションサイジング | 0.5-1.0% リスク |
| 損切り (SL) | **VA edge を抜けた地点 + 2×ATR** |
| 利確 (TP) | **POC (Point of Control)** = 統計的に最も「磁石」効果が強い価格 |
| 最大同時ポジション | 2 (異なるペア) |
| 想定 MaxDD | 12-18% |

## 6. 自己改善メカニズム [G0-B] — 必須

### ドリフト検出
- **VA edge ヒット率**: 過去30トレードで「VAL タッチ後の反転 → 成功」率が 50% 切ったら警戒
- **Volume Profile の形状変化**: POC が日中で大きく動く (trending market) と Value Area 戦略は機能しない → 期間判別
- **Tick Volume と実出来高の解離**: BIS データ等で相関悪化を検出 (年次)

### 自動再最適化
- **月次パラメータ最適化** (Optuna):
  - Value Area 比率 (60/70/80%)
  - bins 数 (30/50/80)
  - RSI 反転確認閾値 (35/40/45)
  - SL/TP 比率 (1:1, 1:1.5, 1:2)
- **「Trending 期は停止」フィルタ**: ADX > 30 または日次レンジ拡大時に取引停止

### フォールバック
- **新パラメータ OOS PF < 直前パラメータ × 0.8** → ロールバック
- **2週間連続 PF < 0.8** → 取引停止 + Volume Profile 設計見直し
- **「Wider VA モード」**: Value Area 80% に拡大して取引頻度を下げる

## 7. 過去 BT 結果 [G0-A] — 必須

### 既存研究の参照
- **QuantifiedStrategies "Order Flow Trading Strategy"**: 体系的バックテスト、ただしFX特化は限定的 ([QuantifiedStrategies](https://www.quantifiedstrategies.com/order-flow-trading-strategy/))
- **CMC Markets "Order Flow Trading Guide"**: 戦略概要 ([CMC Markets](https://www.cmcmarkets.com/en/trading-strategy/order-flow-trading))
- **Trader Dale "Volume Profile Forex"**: 専門教育コース、複数の事例検証あり ([Trader Dale](https://www.trader-dale.com/volume-profile-forex-trading-course/))
- **LuxAlgo "Volumetric Order Flow Structure"**: 指標実装 ([LuxAlgo](https://www.luxalgo.com/library/indicator/volumetric-order-flow-structure/))
- **ATAS Software**: プロ向け Order Flow ツール、time machine 機能で BT 可能 ([ATAS](https://atas.net/))

### PF > 0.95 を超える論拠
- Trader Dale 等のコミュニティで **PF 1.2-1.5** の実例多数 (公開された詳細BTは限定)
- POC への「magnet effect」は microstructure 理論的に確立
- **問題点**: FX の OTC 構造 → Tick Volume が「真の出来高」ではない → 戦略有効性が他市場 (futures) より低い可能性

### 自前 BT 提案
- 過去2年 EUR/USD M5 で Volume Profile + VA edge 戦略を実装
- Tick Volume vs CME EUR/USD futures volume の相関を測定 (代理指標妥当性検証)
- 累計 PF を測定 (スプレッド 1.0pip 込み)

## 8. WFA / OOS [G1-7]

- **Walk-Forward**: 12ヶ月学習 / 3ヶ月運用、3年で 8サイクル
- **取引頻度**: VA edge ヒットは1日1-3回 → 3年で 900-2700 トレード
- **Trending vs Range 期間別評価**: ADX による期間分割で PF を別々に集計
- **Stress Test**: Brexit 2016, COVID 2020, GBP event 2022 等で Value Area の崩壊度合いを確認

## 9. 実装複雑度 [G1-3]

- **工数見積もり**: 3週間
  - Week 1: Volume Profile 計算ライブラリ実装
  - Week 2: VA edge 検出 + シグナル生成 + フィルタ
  - Week 3: Optuna + バックテスト + WFO
- **依存ライブラリ**: `mt5, numpy, pandas, optuna, ta`
- **外部 API 依存**: MT5 のみ
- **既存資産活用**: ゼロから (亡き者と全く別系統)

## 10. 機会費用比較 [G1-6]

| 対象 | 想定年率 | 100万円運用時 / 年 |
|---|---|---|
| 米国債 4% | 4.0% | 40,000 JPY |
| 全世界株 8% | 8.0% | 80,000 JPY |
| 銀行預金 | 0.05% | 500 JPY |
| **本戦略 (期待値)** | **8-18%** (PF 1.2-1.5, MaxDD 中位) | **80,000-180,000 JPY** |

シンプル × 多数取引で月 30-90 トレード → 統計的に有意な収益化が期待できる。

## 11. リスク・既知の弱点

1. **Tick Volume ≠ 真の出来高**: FX の OTC 構造で、ブローカー間の tick 数差異あり (代理指標としての限界)
2. **Trending Market で機能しない**: 強トレンド時は POC が移動し続け、反転戦略は損失
3. **Mainstream 戦略のリスク**: 多くの参加者が同じ VA edge を意識 → stop hunt の標的
4. **時間軸の選択**: 日次 vs 週次 vs 月次 Volume Profile で結果が大きく変わる
5. **Liquidity Provider 依存**: ブローカーごとに tick_volume が異なる (再現性低い)
6. **データ容量**: M5 過去2年 = 数十万バー × 複数ペア で計算負荷
7. **亡き者の世界との関係**: **完全に別系統**、亡き者の失敗パターン非継承

## 12. 採点自己評価

### Gate 0 (必須)

| 項目 | 評価 | コメント |
|---|---|---|
| **G0-A**: PF > 0.95 | **△** | コミュニティ事例多数だが、学術的検証は限定。FX 適用の限界あり |
| **G0-B**: 自己改善 | **○** | Optuna 月次 + Trending フィルタ + ロールバック + Wider VA mode |

→ **Gate 0 = 条件付き PASS** (FX での Tick Volume 妥当性検証必須)

### Gate 1 (各10点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G1-1 想定エッジ源 | 6 | microstructure 理論ベース、FX 適用は限定的、futures ほどクリーンでない |
| G1-2 データ要件 | 8 | MT5 のみ、tick_volume も標準取得可 |
| G1-3 実装複雑度 | 7 | 3週間、Volume Profile 計算は標準的 |
| G1-4 ロバスト性 | 5 | Trending 時に脆弱、ブローカー依存性 |
| G1-5 リスクプロファイル | 7 | VA edge ベースの SL は自然、SL 抜け時の損失限定 |
| G1-6 機会費用比較 | 6 | 期待 8-18% は中位 |
| G1-7 WFA / OOS | 7 | 8サイクル、サンプル豊富、Trending 別評価要 |

**Gate 1 = 46/70**

### Gate 2 (各5点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G2-1 スプレッド耐性 | 3 | M5 ベースで取引頻度多、スプレッド影響中 |
| G2-2 他戦略との相関 | 4 | 反転戦略 = トレンドフォロー系と低相関、分散源 |
| G2-3 説明可能性 | 4 | 「VA edge で反転」は説明可能、ただし「なぜ?」の根拠は弱い |
| G2-4 レビュー耐性 | 3 | 「FX で Volume Profile?」と反論される可能性 |
| G2-5 拡張性 | 4 | 時間軸・ペア拡張可、ブローカー固有性で部分制約 |
| G2-6 過去挙動データ整合 | 3 | 亡き者と別系統、整合性確認不可 |

**Gate 2 = 21/30**

### 総合

| Gate | 点数 | 合否 |
|---|---|---|
| Gate 0 | 条件付き PASS | Tick Volume 妥当性検証必須 |
| Gate 1 | 46/70 | **進出基準 (50点) ぎりぎり未達** |
| Gate 2 | 21/30 | 加点 |
| **総合** | **67/100** | **Phase 1 進出 ボーダーライン (70点未達)** |

### 結論
**理論的に興味深いが、FX での実用性に疑問が残る**。Tick Volume が真の出来高ではないこと、Trending 期で機能しないことが構造的弱点。**他候補で 80+ がある中、優先度は低**。Phase 1 進出は保留、他候補 (meta-labeling, cointegration, London breakout) のあと、補完戦略として再評価が現実的。

---

## ソース

1. [Order Flow Trading Strategy – Backtest Analysis](https://www.quantifiedstrategies.com/order-flow-trading-strategy/) - QuantifiedStrategies
2. [Order Flow Trading Guide: Strategies for Traders](https://www.cmcmarkets.com/en/trading-strategy/order-flow-trading) - CMC Markets
3. [Trader Dale's Volume Profile Forex Trading Course](https://www.trader-dale.com/volume-profile-forex-trading-course/)
4. [ATAS - Order Flow & Volume Analysis Software](https://atas.net/)
5. [Volumetric Order Flow Structure Indicator - LuxAlgo](https://www.luxalgo.com/library/indicator/volumetric-order-flow-structure/)
6. [Order Flow Trading & Volumetric Bars - NinjaTrader](https://ninjatrader.com/trading-platform/free-trading-charts/order-flow-trading/)
7. [How to Trade Using Volume Profile and Order Flow](https://www.trader-dale.com/how-to-trade-using-volume-profile-and-order-flow-a-step-by-step-strategy/)
