# Step B 文献調査結果 — A群「フレーム」(H1 + H3)

> **対象仮説**: H1 (3状態モデル) / H3 (M15/H1/D1 三層)
> **調査日**: 2026-05-08
> **調査エージェント**: researcher (subagent)
> **次段階**: Step C 三角測量 (本ファイル × HYPOTHESES_2-1.md × 自前検証データ)

---

## 仮説 H1: 3状態モデル

### 主要文献

| # | 文献 | 影響 |
|---|---|---|
| 1 | [Hamilton (1989)](https://users.ssc.wisc.edu/~behansen/718/Hamilton1989.pdf) Markov-switching の原典。**2状態（拡張・後退）** で GNP 非定常性を説明 | **未決〜やや反論** |
| 2 | [Ang & Bekaert (2002)](https://business.columbia.edu/sites/default/files-efs/pubfiles/1971/1137.pdf) International Asset Allocation With Regime Shifts。bivariate/trivariate (2/3状態) 両方試す。後続 (2004) で2状態に収束 | **弱い支持** |
| 3 | [Lee et al. (2023) BoE WP No.1042](https://www.bankofengland.co.uk/-/media/boe/files/working-paper/2023/foreign-exchange-hedging-using-regime-switching-models-the-case-of-pound.pdf) GBP/USD/EUR/JPY/TRY に **4状態 (very low / low / high / very high)** モデル。長期トレンド乖離方向×大きさで定義 | **反論寄り** |
| 4 | [MDPI JRFM (2020)](https://www.mdpi.com/1911-8074/13/12/311) Regime-Switching Factor Investing with HMM。HMM 2-6状態を比較。**AIC/BIC + 経済的解釈** で状態数決定すべきと結論 | **未決（方法論的補強）** |
| 5 | [LuxAlgo HMM Market Regimes](https://www.luxalgo.com/library/indicator/hidden-markov-model-market-regimes/) 実務 HMM は **4状態が標準**: Low-Vol Trend / High-Vol Chop / Crash / Accumulation | **反論寄り** |

### 結論

**支持強度: ★★☆（中程度〜弱い支持）**

学術系では2状態が主流（Hamilton, 後期 Ang&Bekaert）、最新FX実証 (BoE 2023) は4状態、実務 HMM も4状態が多い。**3状態は「中庸」で、特に強い文献的根拠はない**。

**対立解釈**:
- **(a) 「方向 × ボラ」の 2×2 = 4状態** が最低限という主張（BoE/LuxAlgo） → trending/ranging を方向軸に、volatile はボラ軸に分けるべき
- **(b) 2状態（高ボラ vs 低ボラ）** で十分（Hamilton 系の純学術）
- **(c) 3状態は「人間の認知に馴染みやすく実務的」だが統計的最適ではない** 可能性

### Step C で当たるべき検証

1. **HMM/MS-AR を 2/3/4/5 状態で当てはめ、BIC を比較**（statsmodels の MarkovAutoregression 等）
2. **4状態 = (trend × low-vol)(trend × high-vol)(range × low-vol)(range × high-vol)** で当てはめ、3状態モデルとの out-of-sample 予測力 (HitRate / Brier score) を比較
3. **「volatile」状態が trending とも ranging とも独立に動いているか**（相関分析）。独立でなければ「volatile」は冗長な軸

---

## 仮説 H3: M15 / H1 / D1 三層

### 主要文献

| # | 文献 | 影響 |
|---|---|---|
| 1 | [Elder Triple Screen](https://admiralmarkets.com/education/articles/forex-strategy/triple-screen-trading-system) 三層を **factor of 4-5（4〜5倍刻み）** で配置。標準 W/D/H or D/4H/H | **部分支持 + 部分反論** |
| 2 | [Peters Fractal Market Hypothesis](https://www.edgarepeters.com/blog-2-2/blog-post-title-one-sf2m5) / [Kristoufek (2012) arxiv](https://arxiv.org/pdf/1203.4979) 市場は数秒〜数年の異なるホライズンの参加者から構成 | **三層自体は支持、長期軸の重要性で部分反論** |
| 3 | [ScienceDirect (2014) Fractal markets: Liquidity and time horizons](https://www.sciencedirect.com/science/article/abs/pii/S0378437114002842) 投資家ホライズン多様性が流動性供給の主因 | **三層支持、層数 N=3 は恣意的** |
| 4 | [FXEmpire MTF Analysis](https://www.fxempire.com/education/article/what-is-multi-timeframe-analysis-how-to-align-weekly-daily-and-hourly-charts-1583933) / [Tradeciety](https://tradeciety.com/how-to-perform-a-multiple-time-frame-analysis) デイトレ標準は **15m/1h/4h** または **5m/15m/1h**。比率おおむね4倍 | **部分支持 + 部分反論** |
| 5 | [Bookmap MTF Guide](https://bookmap.com/blog/multi-time-frame-analysis-a-guide-for-traders) 「**少なくとも週足または日足から始めよ**（top-down approach）」。デイトレでも文脈把握に W1 を使う論者多数 | **反論寄り** |

### 結論

**支持強度: ★★☆（三層自体は支持、構成と比率は要再考）**

- 「三層が必要十分」: **支持される**（Elder, FMH, 実務多数派が3〜4層を推奨）
- 「M15/H1/D1 の組み合わせ」: **部分支持**。ただし **比率の偏り（4倍 vs 24倍）はフラクタル分析的に問題**。Elder 流（4-5倍刻み）に従うなら **M15/H1/H4** (4倍×4倍) や **H1/H4/D1** (4倍×6倍) のほうが整合的
- 「W1/MN は不要」: **反論が強い**。FMH/実務 top-down 派から W1 を「環境認識フィルター」として残せという指摘多数

**対立解釈**:
- (a) Elder 流: 比率は 4-5 倍で揃えるべき → M15/H1/H4 か H1/H4/D1
- (b) FMH 流: 投資ホライズンは多様で、W1/MN も独立な情報源
- (c) 実務 top-down 派: W1 は intraday の whipsaw 回避と SL/TP 水準設計に効く
- (d) 反論: 個人デイトレで W1 シグナルを取り入れると更新頻度が低すぎてノイズに埋もれる（自前設計を支持）

### Step C で当たるべき検証

1. **比率歪みの実害検証**: M15→H1=4倍、H1→D1=24倍 のギャップで「H1 と D1 の間に情報空白」が生じていないか。同データに **H1/H4/D1 (4倍×6倍)** で当てはめて季節判定の安定性を比較
2. **W1 の incrementally informativeness 検証**: W1 のレジームを feature に追加した場合、M15 リスク管理（SL距離、ロット）の損益が改善するかバックテスト
3. **D1 と W1 のレジーム遷移行列比較**: W1 が D1 の集約でしかなければ冗長、独立な情報があれば残す
4. **W1 サポレジの intraday 効力検証**: W1 主要サポレジ ±50pips 圏内での M15 取引 Win Rate を比較

---

## 全体所見

- **H1 (3状態)**: 文献的には「中庸で根拠が弱い」。最新研究 (BoE 2023) と実務 HMM は **4状態（方向×ボラ）** が主流。3状態のままなら **BIC で他の状態数より優位であることを実データで示す手続き** が必要
- **H3 (M15/H1/D1)**: 三層構造は強く支持されるが、**比率の偏り（24倍ギャップ）** と **W1/MN を切り捨てる強い主張** には文献的な反論材料が複数ある。Elder 流の比率調整 or W1 を「環境認識 only」として軽量に残す設計が穏当

## 信頼性評価

- **一次・査読論文**: 5本（Hamilton 1989, Ang&Bekaert 2002, BoE WP 2023, MDPI JRFM 2020, ScienceDirect 2014）
- **実務文献・教科書系**: 4+本（Elder Triple Screen 解説群, FXEmpire, Tradeciety, LiteFinance, LuxAlgo）
- **注意点**: LuxAlgo / Volatility Box は実務系ベンダー記事で検証バイアスあり。BoE ペーパーの4状態は「方向×大きさ」で「方向×ボラ」ではない点に留意（混同しないこと）
