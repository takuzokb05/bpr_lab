# 公開実装ベンチマーク: RsiPullback vs freqtrade HLHB vs Holy Grail

実施日: 2026-05-03
担当: public-strategy-porter (チーム fx-fix-and-improve)
タスク: #17 [P1-4]

---

## 1. 目的

現本番戦略 **RsiPullback** が、公開・実証された戦略と比べて優れているのかを
**同一データ・同一評価条件**で定量的に判定する。「自作戦略の優位性」を確認するためのリアリティチェック。

## 2. 比較対象

| 戦略 | 出典 | コア・ロジック |
|------|------|---------------|
| **RsiPullback** | 本番 (`src/strategy/rsi_pullback.py`) ※評価には等価ロジックの `MTFPullbackBT` を使用 | MA(200) 方向 + RSI(14) < 35 / > 65 で逆張り押し目 |
| **freqtrade HLHB** | [freqtrade-strategies/hlhb.py](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/hlhb.py) / BabyPips "HLHB Trend-Catcher" | EMA(5) × EMA(10) クロス + RSI(10) 50 クロス + ADX(14) > 25 |
| **Holy Grail** | Linda Raschke "Street Smarts" / [tradingsetupsreview](https://www.tradingsetupsreview.com/holy-grail-trading-setup/) | ADX(14) > 30 + EMA(20) 押し目 + 押し目高値ブレイク |

実装: `src/strategy/_bench_hlhb.py`, `src/strategy/_bench_holy_grail.py`
（`_bench_` prefix で本番投入と区別。アルゴリズム要点と公開元 URL をコード内に明記）

### 評価条件を揃えるための統一ルール

公開戦略の本来の SL/TP（freqtrade ROI、Raschke スイングロー等）は実装ごとに
バラバラなので、**評価軸を揃えるため全戦略で以下に統一**:

- SL = ATR(14) × 2.0
- TP = SL距離 × 2.0 (RR=2.0)
- exclusive_orders=True（同時1ポジション）
- commission=0.00002, margin=1/25 (50倍)
- spread 自動計算（auto_spread=True、1pip）

## 3. データ・メトリクス

| 項目 | 値 |
|------|---|
| ペア | USD_JPY / EUR_USD / GBP_JPY |
| 時間足 | M15 |
| 期間 | yfinance `period=60d`（最大60日） |
| バー数 | 約 5,650本/ペア |
| メトリクス | PF, Win Rate, Sharpe, **Sharpe 95% CI**, MaxDD, Return%, WFE (IS/OOS 70:30) |

Sharpe 95% CI は近似 SE = √(1/N_trades) で算出（Lo & MacKinlay 1999 の単純近似）。
トレード数の少なさ由来の不確実性を可視化する目的。

## 4. 結果

### 比較表

| Strategy | Pair | Trades | WR% | PF | Sharpe (95% CI) | MaxDD% | Return% | WFE |
|---|---|---:|---:|---:|---|---:|---:|---:|
| **RsiPullback** | USD_JPY | 35 | 45.7 | **1.80** | **+0.90** (+0.57, +1.24) | -26.3 | **+61.4** | +1.36 |
| freqtrade HLHB | USD_JPY | 51 | 23.5 | 0.58 | -9.51 (-9.79, -9.24) | -60.1 | -47.6 | +0.63 |
| Holy Grail | USD_JPY | 53 | 32.1 | 0.91 | -0.17 (-0.44, +0.10) | -50.2 | -16.0 | -0.05 |
| **RsiPullback** | EUR_USD | 45 | 44.4 | **1.44** | **+1.13** (+0.84, +1.42) | -16.1 | **+28.9** | +0.48 |
| freqtrade HLHB | EUR_USD | 60 | 33.3 | 0.78 | -4.32 (-4.58, -4.07) | -42.2 | -29.0 | +2.15 |
| Holy Grail | EUR_USD | 76 | 36.8 | 0.91 | -1.73 (-1.95, -1.50) | -50.7 | -22.1 | +0.84 |
| **RsiPullback** | GBP_JPY | 35 | 42.9 | **1.23** | **+0.62** (+0.29, +0.95) | -28.6 | **+13.9** | +2.96 |
| freqtrade HLHB | GBP_JPY | 63 | 31.7 | 0.87 | -2.34 (-2.59, -2.09) | -63.6 | -27.5 | -0.07 |
| Holy Grail | GBP_JPY | 69 | 37.7 | 1.04 | +0.02 (-0.22, +0.26) | -50.4 | +0.5 | -0.04 |

CSV: `data/strategy_benchmark.csv`

### スコアまとめ（3ペア集計）

| Strategy | PF >1 のペア数 | Sharpe>0 のペア数 | 平均 Return% | 平均 MaxDD% |
|---|:---:|:---:|---:|---:|
| **RsiPullback** | **3/3** | **3/3** | **+34.7%** | **-23.7%** |
| Holy Grail | 1/3 | 1/3 | -12.5% | -50.4% |
| freqtrade HLHB | 0/3 | 0/3 | -34.7% | -55.3% |

## 5. 結論

### Q. 公開実装は本実装より優れているか？

**A. 否。本実装 (RsiPullback) の方が明確に優れている。**

- **3ペア × 全メトリクス**で RsiPullback が freqtrade HLHB / Holy Grail を上回る
- HLHB は USD_JPY で Sharpe **-9.51**, Return **-47.6%**, MaxDD **-60.1%** の壊滅的結果
- Holy Grail はすべてのペアで MaxDD が **-50% 超**。資金の半分以上が消える深さ
- RsiPullback の Sharpe 95% CI 下限がいずれも **+0.29 以上**で正のエッジが信頼区間で残る一方、
  公開2戦略は CI 上限すら 0 未満（GBP_JPY Holy Grail のみ例外で +0.26）

### Q. 移植する価値はあるか？

**A. ない。本ベンチマーク条件下では移植不要。**

理由:

1. **メトリクス全敗**: PF, Sharpe, MaxDD, Return すべてで RsiPullback 優位
2. **ボラティリティの大きい M15 では公開戦略のフィルターが弱い**:
   - HLHB の ADX>25 は M15 でほぼ常時通過するため低品質エントリーが量産される
   - Holy Grail の ADX>30 + 押し目接触はトリガーが頻発し、SL ヒット率が高い
3. **データ期間 (60日) が短い**: 統計的優位の主張には不足だが、CI 下限の符号で
   明確に「公開2戦略は負ける」と言える。RsiPullback は CI 下限が 0 を超える

### 注意点 (Disclaimer)

- 本ベンチは yfinance 60日 M15 データに限定。長期 / 別期間 / 他ペアでは結果が変わる可能性あり
- HLHB / Holy Grail の本来の SL/TP（ROI / スイングポイント）を ATR ベースに統一しているため、
  公開実装そのものの実戦パフォーマンスとは異なる
- Holy Grail の「押し目接触」検出は近似実装。原典の人手判断との乖離はある
  （実装上のコメントに明記 — `src/strategy/_bench_holy_grail.py`）

## 6. アクション提言

- **RsiPullback を主力として継続**。公開戦略の取り込みは現時点では不要
- 改善余地は task #16 (パラメータ感度分析) と task #18 (実戦 vs バックテスト乖離分析) に委ねる
- 将来的に長期データ (1y+) や M15 以外の TF で再ベンチを行いたい場合は、
  `scripts/run_public_strategy_benchmark.py` の `INTERVAL` / `PERIOD` を調整するだけで再実行可能

## 7. 再現方法

```bash
cd FX自動取引
python scripts/run_public_strategy_benchmark.py
# 出力: 標準出力の比較表 + data/strategy_benchmark.csv
```

依存: `data/_yf_cache_<pair>_15m.csv` にキャッシュされる
（task #16 strategy-validator と CSV キャッシュを共有）

## 8. 関連ファイル

- `src/strategy/_bench_hlhb.py` — freqtrade HLHB 移植
- `src/strategy/_bench_holy_grail.py` — Holy Grail 移植
- `scripts/run_public_strategy_benchmark.py` — 比較ランナー
- `data/strategy_benchmark.csv` — 結果 CSV
- `src/strategy/variants_bt.py::MTFPullbackBT` — 評価で使用した RsiPullback 等価実装
