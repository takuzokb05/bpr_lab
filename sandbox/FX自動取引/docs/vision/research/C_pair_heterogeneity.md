# Step B 文献調査結果 — C群「ペア性質」(H4)

> **対象仮説**: H4 (ペア別閾値)
> **調査日**: 2026-05-08
> **調査エージェント**: researcher (subagent)
> **次段階**: Step C 三角測量

---

## 仮説 H4: ペア別閾値仮説

### 主要文献

| # | 文献 | 影響 |
|---|---|---|
| 1 | [Andersen & Bollerslev (1997, 1998)](https://public.econ.duke.edu/~boller/Published_Papers/joef_00.pdf) "Intraday periodicity and volatility persistence" Journal of Empirical Finance。5分足FX に **Flexible Fourier Form (FFF)** で fit すると **FX ボラのうちかなりの分散が「時間帯」だけで説明される** | **部分的反論** |
| 2 | [Ito & Hashimoto (2006)](https://www.nber.org/system/files/working_papers/w12413/w12413.pdf) "Intra-Day Seasonality in FX Markets" NBER WP 12413。EBS データで **USD/JPY と EUR/USD の intraday パターンが質的に異なる**。**「日本指標発表ではボラが上がらず、米国指標で大幅に上がる」** という非対称性 | **強支持** |
| 3 | [Menkhoff, Sarno, Schmeling, Schrimpf (2012)](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2012.01728.x) "Carry Trades and Global Foreign Exchange Volatility" JoF。**グローバル FX ボラが cross-section の共通リスクファクター**。同じ「ボラ上昇イベント」でも通貨ごとにエクスポージャの**符号も大きさも違う** | **強支持** |
| 4 | [Brunnermeier, Nagel, Pedersen (2008)](https://www.nber.org/system/files/working_papers/w14473/w14473.pdf) "Carry Trades and Currency Crashes" NBER。**キャリートレードは負の歪度（クラッシュリスク）を持ち、その歪度は通貨ペアによって大小が違う**。GBP/JPY のような high-yield × funding currency クロスはテイル特性が突出 | **強支持（テイル側）** |
| 5 | [Krohn (2024)](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306) "Foreign Exchange Fixings and Returns around the Clock" JoF。**時間帯効果と通貨ペア効果がともに有意で、両方を separately にコントロールしないとリスク管理が歪む** | **中立 → 弱支持** |

**補足（実務的根拠）**:
- [BIS Triennial Survey 2022](https://www.bis.org/statistics/rpfx22_fx.pdf) — USD/EUR 1019B/日, USD/JPY 439B, USD/GBP 543B。**JPY ペアは EUR より流動性低い**
- [Ranaldo & Santucci (2022)](https://www.sciencedirect.com/science/article/pii/S0304405X22001891) "Liquidity in the global currency market" JFE。**USD < EUR < JPY < GBP の順で価格インパクトが大きい**

### 結論

**支持強度: ★★★★（強支持寄り）**

- ペア別にボラの「絶対水準」「分布形状（歪度・尖度）」「ファクター loading」「流動性深度」がすべて異なるという実証的合意は強い (Menkhoff 2012, Brunnermeier 2008, Ranaldo 2022, BIS 2022)
- ただし**「時間帯効果」も同時に支配的**(Andersen-Bollerslev, Ito-Hashimoto, Krohn 2024)。**「ペア別 vs 時間帯別」はトレードオフではなく直交**。既に M15 三層 + 時間帯フィルタを持っているなら、ペア別閾値は補完として正当化される
- 1つ星減らした理由: **「ペア別パーセンタイルでよいのか、それとも絶対水準でないとダメか」までは文献が直接答えていない**。M15 YZ_vol で 30/80/30 のパーセンタイル方式は便利だが、文献的には「絶対水準で見ると JPY クロスがそもそも高ボラ層」という事実があり、パーセンタイルで吸収しきれているか別検証が要る

### 注意すべき対立解釈

1. **「時間帯デシーズナライズで十分」説 (Andersen-Bollerslev 系)**: 5分〜時間足では intraday 周期が分散の大半を占める。M15 ならまずこっちを除いてからペア別閾値の必要性を検証すべき
2. **「ボラは1ファクター」説 (Menkhoff 2012)**: global FX volatility がドミナントファクター。各ペアの YZ_vol は global vol への loading × ペア固有 = 単一ファクターで近似可能かもしれない → **「global vol レジーム × ペア loading」** という設計の方が parsimonious
3. **「データスヌーピング」反論**: H4 採用動機が「検証で各ペア最適値が違ったから」なら事後選択。**out-of-sample で同様に最適値が違うか** が分かれ目（H7 と接続）

### Step C で当たるべき検証

1. **一律閾値 baseline との比較**: 3ペア共通の絶対パーセンタイル（プールしたサンプルの 30/80/30）vs 現状のペア別閾値で、out-of-sample TR / PF を比較。**ΔTR < 0.05 なら H4 棄却**
2. **時間帯デシーズナライズ後の再評価**: M15 YZ_vol を Flexible Fourier or hour-of-week dummy で deseasonalize した「残差ボラ」でも閾値差が残るか。残らなければ「ペア別」ではなく「時間帯別」が真因
3. **パーセンタイル方式の sanity check**: 各ペアで 80パーセンタイル日のヒストグラムを並べる。GBP/JPY の 80%ile day と EUR/USD の 80%ile day のレジーム特性が違うなら、パーセンタイル正規化は不十分
4. **Factor 分解 (PCA)**: 3ペアの YZ_vol を「global vol factor + pair-specific」に分解し、pair-specific 成分が閾値判断にどれだけ寄与しているかを定量化

### 一言サマリ

**H4 は文献的にほぼ支持される（特に Menkhoff 2012, Brunnermeier 2008, Ito-Hashimoto 2006, Ranaldo 2022 が直接的根拠）。ただし「ペア別 *パーセンタイル*」の妥当性と「時間帯効果との分離」の2点は文献が直接答えておらず、Step C で検証すべき。最大の対立解釈は Andersen-Bollerslev の「intraday 周期で大半説明できる」線で、デシーズナライズ後にも閾値差が残るかが H4 サバイバルの試金石。**
