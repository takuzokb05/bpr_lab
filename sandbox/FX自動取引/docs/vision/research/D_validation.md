# Step B 文献調査結果 — D群「検証手続き」(H5 + H6)

> **対象仮説**: H5 (TR>1.0 合格基準) / H6 (単一分割 walk-forward)
> **調査日**: 2026-05-08
> **調査エージェント**: researcher (subagent)
> **次段階**: Step C 三角測量

---

## 仮説 H5: TR > 1.0 合格基準

### 主要文献

| # | 文献 | 影響 |
|---|---|---|
| 1 | [TradingView Profit Factor 公式](https://www.tradingview.com/support/solutions/43000681698-profit-factor/) **PF = Gross Profit / Gross Loss**。実務では **1.5 以上を「健全」**、**1.5–3.0 が retail trader の標準合格ライン** | **反論** |
| 2 | [PyBroker Bootstrap Confidence Interval](https://www.pybroker.com/en/latest/notebooks/3.%20Evaluating%20with%20Bootstrap%20Metrics.html) **per-bar resampling + BCa bootstrap で PF の CI を構成**。CI 下限が 1 を割れば不採用 | **支持（運用方法）** |
| 3 | [TradesViz Hit Ratio](https://www.tradesviz.com/glossary/hit-ratio/) Hit Ratio = Winning Trades / Total Trades。**単独評価不適、reward-risk と併用必須** | **反論** |
| 4 | [Romano & Wolf (2005)](http://www-stat.wharton.upenn.edu/~steele/Courses/956/Resource/MultipleComparision/RomanoWolf05.pdf) Econometrica。**studentized stepwise multiple testing**。閾値スイープ等で複数 TR を比較する場合は**FWER 制御が必須** | **未決→反論寄り** |

### 結論

**支持強度: ★☆☆（反論強）**

- TR の自前定義 = (片側平均/片側平均) は、**Profit Factor (gross/gross) でも Sharpe でも AUC でもない**。最も近いのは「片側別 Profit Factor」または「条件付き期待値の比」
- **対立解釈**: 1.0 は赤字との境界線にすぎず、コスト・スリッページ・選択バイアスを織り込むと**少なくとも 1.3–1.5 が下限**。1.05 と 1.0 の差は信号でなくノイズ
- 閾値グリッドサーチで「TR > 1.0」を見たペアは選択バイアス膨張済み、生 TR 値は虚偽で **Romano-Wolf 多重補正後 p 値**で判定すべき

### Step C で当たるべき検証

1. 自前 TR の数式を **Profit Factor または期待値比**に書き直し、文献用語にマッピング
2. **BCa bootstrap で CI 下限を計算**、1.0 超の指標のみ採用（PyBroker 方式）
3. 閾値スイープで複数候補を比較した場合は **Romano-Wolf 補正**で familywise p < 0.05 のものだけ通す
4. 二群比較の自然な統計検定として **Welch t-test (平均) + Mann-Whitney U (中央値)** の二段確認

---

## 仮説 H6: 単一分割 walk-forward

### 主要文献

| # | 文献 | 影響 |
|---|---|---|
| 1 | [López de Prado (2018) AFML + CPCV](https://en.wikipedia.org/wiki/Purged_cross-validation) **Combinatorial Purged Cross-Validation**: N 個のテストパスを構成し**OOS 性能の分布**を得る、purge + embargo で leakage 排除 | **強い反論** |
| 2 | [Hansen (2005) SPA test](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=264569) White Reality Check の改良版、**studentized + sample-dependent null** で poor alternative の影響を排除 | **反論** |
| 3 | [Unger Academy Anchored vs Rolling WFA](https://ungeracademy.com/posts/how-to-use-walk-forward-analysis-you-may-be-doing-it-wrong) / [Robust Trader](https://therobusttrader.com/walk-forward-analysis-testing-optimization-wfa/) **Anchored**: IS 起点固定で拡張、長期戦略向き / **Rolling**: IS 窓を一定幅で前進、レジーム変化追従向き | **部分反論** |
| 4 | [arXiv 2512.12924 (2025)](https://arxiv.org/html/2512.12924v1) + [BSIC Cross-Validation](https://bsic.it/backtesting-series-episode-2-cross-validation-techniques/) 時系列 CV では **k-fold (k=5–10) を温存**しつつ**purged + embargoed**化、または expanding/rolling WFA で**最低 5 fold**で TR/Sharpe/PF の分布集計 | **反論** |

### 結論

**支持強度: ★☆☆（反論強）**

- 単一 IS/OOS 分割は **k=1 の k-fold**で、Pardo 2008 の入門レベル
- **現代の robust validation 標準は CPCV または rolling WFA × 5+ fold**
- **単一分割が許容されるケース**: (a) PoC・最初期検証 / (b) サンプル数が極端に少なく分割不可能 / (c) **独立した forward test (live paper)** で別途検証する前提。仮説検証の**最終判定**には不十分
- **対立解釈**: ロングホライズン戦略 (D1/週足) かつ非定常ペア (USD_JPY 介入レジーム等) では rolling 不安定で anchored が好まれる。**全 fold で同じ閾値が選ばれない**ことそれ自体が H6 の反証

### Step C で当たるべき検証

1. **rolling WFA × 5–8 fold** に置き換えて TR/PF/Sharpe の **分散・95% CI・最悪 fold** を計測
2. ペア・時間軸ごとに**閾値が fold 横断で安定**しているか（一致率・Spearman 相関）を確認 — 不安定なら閾値そのものを疑う
3. 候補閾値を全 fold でグリッド評価し、**Hansen SPA test** で「最良閾値が偶然でない」を確認
4. 余力があれば **CPCV** (mlfinlab / skfolio 実装) で複数 OOS パスの分布まで取り、**PBO (Probability of Backtest Overfitting)** を Bailey 2014 で計算
5. **Anchored vs Rolling の両方走らせて結果収束を見る** — 一致しない指標は採用しない

---

## 自前 TR → 文献標準への具体マッピング

| 自前 TR 定義の解釈 | 文献標準の対応 | 採用基準（実務） |
|---|---|---|
| 平均リターン比 (上側/下側) | 条件付き期待値比 ≒ Profit Factor の派生 | PF > 1.5、BCa CI 下限 > 1.0 |
| 平均勝ちトレード比 | Reward-Risk Ratio に近い | RRR × Win Rate > 1 (期待値正) |
| 勝率比 (上側勝率/下側勝率) | Hit Rate Ratio | 単独不可、payoff と併用 |
| 二値分類精度 | AUC | AUC > 0.55、DeLong 検定 p<0.05 |
| 群間平均差 | Welch t-test | t 統計量 + Mann-Whitney U の二段 |

**最小推奨置換**: 「**TR > 1.0**」→ 「**Profit Factor の BCa bootstrap 95% CI 下限 > 1.0 かつ Romano-Wolf 補正後 p < 0.05**」
