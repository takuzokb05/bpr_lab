# Step B 文献調査結果 — B群「指標選定」(H2 + H7 + H8)

> **対象仮説**: H2 (直交分解) / H7 (三層生存=採用根拠) / H8 (length grid)
> **調査日**: 2026-05-08
> **調査エージェント**: researcher (subagent)
> **次段階**: Step C 三角測量

---

## 仮説 H2: ボラ × トレンドの直交分解

### 主要文献

| # | 文献 | 影響 |
|---|---|---|
| 1 | [Yang & Zhang (2000)](https://www.jstor.org/stable/10.1086/209650) "Drift-Independent Volatility Estimation" Journal of Business 73(3). OHLC を最大活用、最小分散・**ドリフト独立**・始値ジャンプに頑健 | **部分支持（要注意）** |
| 2 | [Dreiss (1992)](https://www.quantifiedstrategies.com/choppiness-index/) Choppiness Index の原典。フラクタル幾何で「効率(trend) vs 非効率(range)」を測る。**ATR の合計と High-Low レンジの比** | **反論の余地あり** |
| 3 | [BIS WP 214](https://www.bis.org/publ/confer08k.pdf) "Evaluating correlation breakdowns during periods of market volatility" 高ボラ期は相関構造変化（correlation breakdown） | **反論寄り** |
| 4 | [Hurst, Ooi, Pedersen (AQR)](https://fairmodel.econ.yale.edu/ec439/hurst.pdf) "A Century of Evidence on Trend-Following" トレンドフォローは "long volatility" だがボラ環境を問わず安定 | **中立〜支持** |

### 結論

**支持強度: ★★☆（条件付き支持）**

- 理論上は YZ_vol（振幅）と CHOP（経路の効率性）は別軸を測っている
- **【重大な構造的弱点】 CHOP の分子に ATR が入っているため、ボラ指標と完全独立ではない**。ATR が大きい強トレンド局面では分子・分母とも増えるが比率は小さくなる、という特殊な数学的結合を持つ
- 学術的に「強トレンド = 高ボラ」の単純関係は否定されているが、レジーム変化時には共動するため独立性は局面依存

### Step C で当たるべき検証

1. **YZ_vol と CHOP の同時分布（散布図）** で各 4 象限のサンプル密度を確認
2. **強トレンド期間の YZ_vol 値分布** を見て、「強トレンド = 必ず高ボラ」が成り立つか反証
3. **合成二層が単独 (YZ_vol のみ / CHOP のみ) を TR で超えるか** の直接比較 = **Task #25 の本質**

---

## 仮説 H7: 三層生存 = 採用根拠 (★最重要・壊滅的)

### 主要文献

| # | 文献 | 影響 |
|---|---|---|
| 1 | [Sullivan, Timmermann, White (1999)](https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00163) "Data-Snooping, Technical Trading Rule Performance, and the Bootstrap" JoF 54(5). Brock et al. (1992) の 26 ルールを 7846 ルールに拡張、White's Reality Check 補正で **OOS の profitability は消失** | **強い反論** |
| 2 | [Bailey, Borwein, López de Prado, Zhu (2014)](https://www.ams.org/notices/201405/rnoti-p458.pdf) "Pseudo-Mathematics and Financial Charlatanism" Notices of AMS. **5年分日次データなら ~7 戦略試すだけで偽陽性が一定確率で出る** | **強い反論** |
| 3 | [Harvey, Liu, Zhu (2016)](https://www.nber.org/system/files/working_papers/w20592/w20592.pdf) "...and the Cross-Section of Expected Returns" RFS 29(1). 多重検定補正後は **t-ratio > 3.0** が必要（従来 2.0 では不十分）。発表バイアス考慮で**金融経済学の主張の多くはおそらく偽** | **強い反論** |
| 4 | [Bailey & López de Prado (2014)](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) "The Deflated Sharpe Ratio" **False Strategy Theorem**: 真のシャープが全て 0 でも、N 個試した中での最大シャープは N の対数オーダーでプラスに膨らむ | **強い反論** |
| 5 | [Hansen (2005)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=264569) "A Test for Superior Predictive Ability" SPA test。Reality Check の改良版 | **方法論的指針** |

### 結論

**支持強度: ★☆☆（極めて脆弱、現時点では採用根拠として弱い）**

- **「三層全層生存 = 採用根拠」は data-snooping の典型パターン**
- **試行空間の試算**: 指標候補 K × length 4 × 時間軸 3 × 閾値グリッド ~10 = K × 120 試行。K = 3-5 なら **360-600 試行**。Bailey-López de Prado の枠組みでは **TR > 1.0 程度の閾値はノイズで容易に達成**
- Yang-Zhang は OHLC を最大活用する設計上「数値的に安定」する。安定 = 偽の三層生存も起きやすい（信号でなくとも分散が小さく閾値を超えやすい）
- **対立解釈**: 三層生存を「市場フラクタル性の同型反映」と解釈する実務派もいる（M15/H1/D1 で同パターンが出るのは指標の頑健性を示す）。ただし学術的裏付けは乏しい

### Step C で当たるべき検証

1. **ランダム指標ベースライン**: ホワイトノイズ・GBM・自己相関ノイズで疑似指標を 100-1000 個生成し、同じ三層生存判定で TR>1.0 を達成する確率を測る → 偶然レートの実測
2. **試行数の文書化**: これまで試したすべての指標・length・閾値の組合せ数 N を記録し、Deflated Sharpe Ratio 相当の補正を TR にも適用
3. **ブートストラップ Reality Check**: STW (1999) 流の手続きで多重検定補正下の p 値を計算
4. **完全 OOS hold-out**: 最終 1-2 年は閾値選定に一切触れずに残し、その期間で TR を再評価
5. **三層生存を「採用根拠」ではなく「採用候補のスクリーニング」に再定義**

---

## 仮説 H8: length grid {10, 14, 20, 30} 妥当性

### 主要文献

| # | 文献 | 影響 |
|---|---|---|
| 1 | [Wilder (1978)](https://archive.org/details/newconceptsintec00wild) "New Concepts in Technical Trading Systems" ATR/RSI/ADX 標準 14 期間の起源。ただし Wilder 自身は **8 期間 ATR** も使用 | **弱い支持** |
| 2 | [Yang-Zhang 実装ガイド](https://trendsandbreakouts.com/yang-zhang-volatility) 安定推定には最低 10-20 期間、実装デフォルト 30 期間が一般的 | **部分支持** |
| 3 | [Pardo (2008)](https://www.quantstart.com/static/ebooks/sat/sample.pdf) "The Evaluation and Optimization of Trading Strategies"。真に頑健なパラメータは **「孤立した山」ではなく「プラトー」** | **強い反論** |
| 4 | [MDPI (2024)](https://www.mdpi.com/2673-4591/74/1/56) "Optimal Parameter Selection and Indicator Design"。粗グリッドはピーク幻影を生む | **反論** |

### 結論

**支持強度: ★★☆（実務標準域はカバー、感度分析として不足）**

- {10, 14, 20, 30} は ATR/RSI 由来の文献標準域に乗っている
- ただし **plateau 検出には 4 点では足りない**。Pardo の robustness 原則に従えば、最低 8-10 点（中間点 12, 16, 18, 22, 25 等）を埋めるべき
- **対立解釈**: フィボナッチ系 (5, 8, 13, 21, 34) や取引日系 (5, 22, 65) など別の根拠を持つ length 体系が存在

### Step C で当たるべき検証

1. {10, 12, 14, 16, 18, 20, 22, 25, 30} の **9 点で TR を再計測 → 単峰性確認**
2. 最良 length 周辺 ±2 で TR が **80% 以上維持されること** を plateau 条件として確認
3. Yang-Zhang の k 重みは period 依存なので **length ごとに k を再計算しているか** をコード確認
4. Wilder が 8 期間も使っていた事実を考慮し、低端 (7, 8) もスポット確認

---

## 全体総括

### 信頼性評価
- **査読論文**: 7 本（Yang & Zhang, Sullivan-Timmermann-White, Bailey 系列, Harvey-Liu-Zhu, Hansen, BIS WP）
- **書籍・実務文献**: 3 本（Wilder, Pardo, Hurst-Ooi-Pedersen）

### 最重要メッセージ（H7 関連）
**「三層生存」を採用根拠と呼ぶのは、現代の金融計量経済学の標準では受け入れられにくい**。Bailey-López de Prado / Harvey-Liu-Zhu / Sullivan-Timmermann-White の枠組みでは、試行数 N の記録と多重検定補正が必須。現状の TR>1.0 単純判定は補正前の名目値であり、deflation 後にどれだけ残るかが問われる。

### 優先度付き次アクション (Step C 候補)

1. **(最優先) 試行回数 N の棚卸し → Deflated TR / Deflated Sharpe 計算**
2. ランダム指標ベースラインで偶然 TR>1.0 達成率を測る
3. length grid を 9 点に拡張して plateau 検証
4. 完全 OOS hold-out 期間を確保（過去 1-2 年を未参照に隔離）
5. YZ_vol × CHOP の同時分布で「直交」を実証 or 反証
