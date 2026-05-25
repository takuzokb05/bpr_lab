# プロポーザル: 通貨ペア コインテグレーション + Bollinger Z-Score 平均回帰

## 1. 戦略仮説

複数の通貨ペアの組み合わせ (例: EUR/USD と GBP/USD、AUD/USD と NZD/USD など) のスプレッド系列が **コインテグレーションしている期間** を識別し、その期間中に **z-score が ±2 を超えたら平均回帰を狙う** 統計的裁定戦略。**スプレッド ≠ 価格そのもの** で取引するためトレンド/レンジ無関係に機能する。

## 2. 想定エッジ源 [G1-1]

- **統計的非効率**: 2通貨ペアの長期均衡関係 (経済的に関連性のあるペア) は短期的に乖離するが、ファンダメンタルが大きく変わらない限り回帰する
- **古典的だが頑健**: Engle-Granger (1987) 以来の数十年の実証 → 構造的優位として確立
- **方向中立**: 上昇相場・下落相場関係なし。**他戦略との相関が極めて低い** → 分散源として価値高
- **既知のリスク**: コインテグレーションは「永続的」ではない。経済構造変化 (例: ブレグジット、コロナ) で関係性が崩れる

## 3. シグナル定義 (擬似コード)

```python
# Stage 1: 候補ペア選定 (1日1回)
candidates = [
    ('EUR/USD', 'GBP/USD'),
    ('AUD/USD', 'NZD/USD'),
    ('USD/CHF', 'EUR/USD'),  # 逆相関活用
    ('USD/CAD', 'AUD/USD'),
]

for pair_a, pair_b in candidates:
    # Engle-Granger テスト
    score, pvalue, _ = coint(pair_a_prices, pair_b_prices)
    if pvalue < 0.05:  # 統計的に共和分
        # Hedge ratio (β) を OLS で推定
        beta = np.polyfit(pair_b_prices, pair_a_prices, 1)[0]
        spread = pair_a_prices - beta * pair_b_prices

# Stage 2: シグナル生成 (1時間ごと)
z_score = (spread - spread.rolling(60).mean()) / spread.rolling(60).std()

# Entry
if z_score > 2.0:
    short(pair_a, lot=1.0); long(pair_b, lot=beta)
elif z_score < -2.0:
    long(pair_a, lot=1.0); short(pair_b, lot=beta)

# Exit
if abs(z_score) < 0.5:  # 平均回帰検出
    close_all()
elif abs(z_score) > 4.0:  # 関係崩壊 → 損切り
    close_all_and_blacklist_pair_24h()
```

## 4. データ要件 [G1-2]

- **必要データ**: 複数通貨ペアの同時刻 H1 OHLCV (3-5ペアセット)
- **取得元**: MT5 (同時刻データ取得が容易)
- **計算リソース**: コインテグレーションテスト = 1秒/ペア、z-score 計算 = ms 級。**極めて軽量**
- **ラグ**: バー閉鎖 + < 1秒

## 5. リスクモデル [G1-5]

| 項目 | 設定 |
|---|---|
| ポジションサイジング | **両ペアで等価値** (lot を hedge ratio で調整) |
| 損切り (SL) | **z-score が ±4 超え** または **24時間経過** で強制 close |
| 利確 (TP) | z-score が ±0.5 以内に回帰 |
| 最大同時ペア数 | 3 (相関リスク管理) |
| 想定 MaxDD | 8-15% (方向中立のため小さい) |
| テールリスク | コインテグレーション崩壊 (例: 通貨ペッグ解除 2015 CHF) → SL 必須 |

## 6. 自己改善メカニズム [G0-B] — 必須

### ドリフト検出
- **コインテグレーションの再検定**: 毎週、過去6ヶ月で Engle-Granger 再テスト。p > 0.05 で **ブラックリスト** (一時除外)
- **β (hedge ratio) の安定性**: ローリング推定値の標準偏差が直近1ヶ月で 50%超増加 → 関係崩壊シグナル
- **z-score 回帰時間**: 半減期 (mean reversion half-life) が 7日以上に伸びたら戦略終了

### 自動再最適化
- **週次ペア再選定**: 候補リスト 20ペアから p < 0.05 を満たすトップ 3-5 を選定
- **z-score 閾値の動的調整**: 過去 3ヶ月の最適 entry 閾値 (1.5/2.0/2.5/3.0) を Optuna で再選定
- **ローリング window 長**: 30/60/120バーから Calmar 比最大のものを選択

### フォールバック
- **3ペア全てがブラックリスト入り** → 取引停止 (= 市場全体でコインテグレーション希薄期)
- **直近 PF < 0.8** → 1週間停止 + ペアリスト見直し
- **「Defensive モード」**: z-score 閾値を 2.5 に上げて取引機会を絞る

## 7. 過去 BT 結果 [G0-A] — 必須

### 既存研究の参照
- **Lemishko, Landi, Caicedo-Llano (SSRN 2024)**: FX ペアコインテグレーション戦略を体系的に検証 ([Cointegration-Based Strategies in Forex Pairs Trading](https://papers.ssrn.com/sol3/Delivery.cfm/4771108.pdf?abstractid=4771108&mirid=1))
- **Pairs Trading + Asymptotic Analyses (Computational Economics 2024)**: 平均回帰収束フィルタ追加で PF 改善 ([Improving Cointegration-Based Pairs Trading Strategy](https://link.springer.com/article/10.1007/s10614-023-10539-4))
- **QuantifiedStrategies (2024)**: USD Bollinger Bands + コインテグレーションで **「PF 最適化が最も高い年率リスク調整リターン」**、ただし 32% のペアは赤字 ([Pairs Trading Strategy](https://www.quantifiedstrategies.com/pair-trading-strategy/))
- **Applied Economics (2018)**: CFD 上でのコインテグレーションペアトレード、PF 最適化で平均 PF > 1.3 ([Pairs trading strategies in a cointegration framework](https://www.tandfonline.com/doi/full/10.1080/00036846.2018.1545080))

### PF > 0.95 を超える論拠
- 既存研究で **PF 1.3-2.0** 報告多数 (ただし黄金期 2010 年代前半中心)
- 2020-2024 は通貨ペッグ崩壊・地政学リスクで一時的にエッジ減少も、**EUR-GBP や AUD-NZD のような構造的近接ペア** では依然有効
- 重要: **「コインテグレーション持続性」 が前提**。これを動的に再検定するから自己改善

### 自前 BT 提案
- 5年分の EUR/USD, GBP/USD, AUD/USD, NZD/USD, USD/CHF, USD/CAD H1 データを取得
- 全 15 ペア組合せで月次コインテグレーション再検定
- z-score 戦略で OOS 累計 PF 測定

## 8. WFA / OOS [G1-7]

- **Walk-Forward**: 12ヶ月学習 (ペア選定 + 閾値最適化) / 3ヶ月運用、5年で 16サイクル
- **複数ペア独立性**: 各ペアで Sharpe を測定し、Sharpe > 0 のペアだけ統合 (ポートフォリオレベル)
- **CPCV**: Combinatorial Purged CV で過剰最適化検出
- **Stress Test**: 2015-01 (CHF event), 2020-03 (COVID), 2022-09 (GBP event) を必ず含む

## 9. 実装複雑度 [G1-3]

- **工数見積もり**: 2週間
  - Week 1: コインテグレーションテスト + z-score シグナル
  - Week 2: WFO + ドリフト検出 + フォールバック
- **依存ライブラリ**: `statsmodels (coint), numpy, pandas, mt5`
- **外部 API 依存**: MT5 のみ
- **既存資産活用**: backtester.py のシグナル発火部分を流用

## 10. 機会費用比較 [G1-6]

| 対象 | 想定年率 | 100万円運用時 / 年 |
|---|---|---|
| 米国債 4% | 4.0% | 40,000 JPY |
| 全世界株 8% | 8.0% | 80,000 JPY |
| 銀行預金 | 0.05% | 500 JPY |
| **本戦略 (期待値)** | **8-15%** (PF 1.3 級、低 DD) | **80,000-150,000 JPY** |

期待値は中位だが **MaxDD 8-15%** が魅力。Calmar 比 (年率/MaxDD) で 1.0-1.5 を狙える。

## 11. リスク・既知の弱点

1. **コインテグレーションの非永続性**: 経済構造変化で関係崩壊 (CHF 2015、Brexit 2016 等の前例)
2. **同方向ポジション**: 2ペア同時保有なのでスプレッドコスト 2倍
3. **証拠金倍要求**: ロング+ショート両建てで MT5 の証拠金が増える
4. **テールリスク**: 関係崩壊時に z-score が ±10 まで暴走することがある (CHF event は 1日で z-score ±30 相当)
5. **小さい収益機会**: z-score ±2 が月数回しか発生しない時期がある
6. **亡き者の世界との関係**: 亡き者は単一ペア戦略、本戦略は別系統。**MTFPullback の失敗パターンを継承しない**

## 12. 採点自己評価

### Gate 0 (必須)

| 項目 | 評価 | コメント |
|---|---|---|
| **G0-A**: PF > 0.95 | **○** | 既存研究で PF 1.3-2.0 報告多数、保守的に PF 1.1-1.4 期待 |
| **G0-B**: 自己改善 | **○** | 週次ペア再検定 + Optuna 閾値最適化 + ブラックリスト機構 |

→ **Gate 0 = PASS**

### Gate 1 (各10点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G1-1 想定エッジ源 | 8 | 統計的非効率、Engle-Granger 以来の実証あり、構造的優位明確 |
| G1-2 データ要件 | 9 | MT5 のみ、複数ペア取得は標準機能 |
| G1-3 実装複雑度 | 9 | 2週間、`statsmodels.coint` のみで実装可能 |
| G1-4 ロバスト性 | 8 | 動的ペア再選定 + ブラックリストで関係崩壊耐性 |
| G1-5 リスクプロファイル | 8 | 方向中立で MaxDD 小、テールリスクは SL で限定 |
| G1-6 機会費用比較 | 6 | 期待 8-15% は控えめ、Calmar 比は優秀 |
| G1-7 WFA / OOS | 8 | 16サイクル WFA、Stress test 込み |

**Gate 1 = 56/70**

### Gate 2 (各5点)

| 項目 | 自己評価 | 理由 |
|---|---|---|
| G2-1 スプレッド耐性 | 3 | 両建てなのでスプレッドコスト 2倍、頻度低めで部分緩和 |
| G2-2 他戦略との相関 | 5 | **方向中立 = 他戦略と圧倒的低相関**。最強の分散源 |
| G2-3 説明可能性 | 5 | 「z-score が±2を超えたら逆張り」と完全に説明可能 |
| G2-4 レビュー耐性 | 5 | 経済学的根拠あり (Engle-Granger)、反論屋耐性高 |
| G2-5 拡張性 | 4 | ペアセット拡大可、エキゾチック通貨追加可能 |
| G2-6 過去挙動データ整合 | 4 | 亡き者単一ペア戦略の失敗を継承しない、独立系統 |

**Gate 2 = 26/30**

### 総合

| Gate | 点数 | 合否 |
|---|---|---|
| Gate 0 | PASS | 既存研究で PF 1.3-2.0 実証 |
| Gate 1 | 56/70 | Phase 2 進出基準クリア |
| Gate 2 | 26/30 | **加点高** (説明可能性 + 低相関) |
| **総合** | **82/100** | **Phase 1 (簡易 BT) 進出 強推奨** |

---

## ソース

1. [Cointegration-Based Strategies in Forex Pairs Trading (SSRN, 2024)](https://papers.ssrn.com/sol3/Delivery.cfm/4771108.pdf?abstractid=4771108&mirid=1) - Lemishko et al.
2. [Improving Cointegration-Based Pairs Trading Strategy with Asymptotic Analyses (Computational Economics 2024)](https://link.springer.com/article/10.1007/s10614-023-10539-4)
3. [Pairs Trading Strategy – Backtest, Trading Rules and Statistics](https://www.quantifiedstrategies.com/pair-trading-strategy/) - QuantifiedStrategies
4. [Pairs trading strategies in a cointegration framework: back-tested on CFD](https://www.tandfonline.com/doi/full/10.1080/00036846.2018.1545080) - Applied Economics (2018)
5. [Cointegration-based pairs trading: identifying ETF (2025)](https://link.springer.com/article/10.1057/s41260-025-00416-0) - Journal of Asset Management
6. [Complete Guide to Backtest Cointegration Pair Trading Strategy](https://medium.com/@mikelhsia/pair-trading-complete-guide-to-backtest-cointegration-pair-trading-strategy-a65da88183eb) - Michael Hsia
