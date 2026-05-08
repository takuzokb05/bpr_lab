# HYPOTHESES — 2-1 季節判定 仮説台帳

> **趣旨**: 2-1 季節判定の検証を**深める前に**、現時点で暗黙に信じていることを明文化する。
> 書いてから検証するのが順序であり、結果から仮説を後付けしない。
> 各仮説には**反証条件**（ポパー流）を併記し、撤回が起きた時にどの結論が連鎖崩壊するかを追跡可能にする。
>
> このドキュメントは `OPERATING_MODEL.md v2.1 § 2-1` と `SPEC_v2.md § 2-1` の**橋**である。
> 数字（SPEC）の前に、なぜその数字が意味を持つと信じているか（HYPOTHESES）を置く。

---

## 文書ステータス

| メタ | 値 |
|---|---|
| 起草日付 | 2026-05-08 |
| 起草段階 | Step A（仮説の明文化） |
| 次段階 | Step B（文献調査）→ Step C（仮説 × 文献 × 検証結果の三角測量） |
| 関連 | `STORY.md` / `PREMISE.md` / `OPERATING_MODEL.md v2.1 § 2-1` / `SPEC_v2.md § 2-1` |
| 関連教訓 | `docs/vision/_archive/LESSON_2026-05-{07,08}_*.md` (5本) |

---

## 用語の定義（先に固定する）

仮説を書く前に、検証で使っている用語を**自前の定義**として固定する。文献用語と合致するかは Step B で確認。

| 用語 | 自前の定義 | 文献での同名概念との整合性 |
|---|---|---|
| **trending レジーム** | 価格が単調方向（上昇 or 下降）に進む期間。CHOP 低値で検出を試みた | 文献では Markov-switching の "trend regime" 等。要確認 |
| **ranging レジーム** | 価格が一定幅を往復する期間。trending でも volatile でもない残余 | 文献では "mean-reverting regime"。要確認 |
| **volatile レジーム** | 価格変動の振れ幅が拡大する期間。YZ_vol 高値で検出を試みた | 文献では "high-volatility regime"。volatile と trending は直交か共起かが論点 |
| **TR (Threshold Ratio)** | 閾値で2分割した時、片側の平均リターン or 平均勝ちトレード成績を、もう片側で割った比 | **これは自前語**。文献での標準名（profit factor, hit ratio 等）と対応するか不明 — Step B で要照合 |
| **IS / OOS** | In-Sample / Out-of-Sample。閾値最適化に使ったデータ / 使っていないデータ | 標準用語 |
| **walk-forward 検証** | IS で閾値決定 → 直後の OOS で評価。本ドキュメントでは**単一分割**のみを使用 | 文献では複数分割の anchored / rolling 形式が標準。差分は H6 で扱う |

**Why（なぜここを最初に固定するか）**: H5・H6 で論点になる「合格基準」と「検証手続き」が、自分の用語で動いているのか文献用語で動いているのかを切り分けられないと、文献調査の照合作業が成立しない。

---

## 仮説の構造

各仮説には以下のフィールドを置く:

- **主張**: 何を信じているか（一文）
- **信じる強さ**: ★1（弱い直感） 〜 ★5（強い確信）
- **信じる理由**: いま手元にある材料
- **反証条件**: どんな結果が出たら撤回するか（先決め）
- **検証ステータス**: 未検証 / 部分検証 / 検証済み（自前データのみ）/ 文献整合確認済み
- **撤回時の連鎖**: この仮説が倒れると一緒に倒れる他仮説・SPEC値
- **関連教訓**: 既存の LESSON_*.md 参照
- **Step B で当たる文献の方向**: キーワードと著者の見当

---

## H1. 3状態モデル仮説

**主張**: 市場の「季節」は **trending / ranging / volatile の3状態**で必要十分である。

**信じる強さ**: ★★（弱い〜中）

**信じる理由**:
- OPERATING_MODEL.md v2.1 § 2-1 で「季節」を語る時、自然に3つの言葉で語った
- 既存 `regime_detector.py` の骨格が3ラベル前提
- 多数の市場解説書（Murphy 等）が trending vs ranging の二分法 + ボラを別軸として扱う

**反証条件**:
- レジーム検出文献の主流が 2状態 or 4状態 で、3状態が「中途半端」と扱われている場合
- 自前検証で「volatile かつ trending」の共起期間が無視できない比率（例: 全期間の20%超）で観察される場合 → H2 と一緒に倒れる
- 4状態（trending-volatile / trending-calm / ranging-volatile / ranging-calm）に拡張すると TR が有意に改善する場合

**検証ステータス**: 未検証（**3状態の必要性そのものを直接検証していない**）

**撤回時の連鎖**: SPEC_v2.md § 2-1 の「三層一致判定スコアリング重み」設計が無効化。`regime_detector.py` 骨格の再設計が必要。

**関連教訓**: なし（このレベルでは検証していない）

**Step B で当たる文献の方向**:
- Hamilton (1989) Markov-switching の状態数選定
- Ang & Bekaert (2002) regime switching in international asset allocation の状態数
- HMM の状態数決定基準（BIC / cross-validation）
- "regime switching FX" "number of regimes" 等の検索

---

## H2. ボラ × トレンドの直交分解仮説

**主張**: ボラティリティ指標 (YZ_vol) で **volatile** レジームを、トレンド指標 (CHOP) で **trending** レジームを担当できる。両者は**直交軸**として機能する。

**信じる強さ**: ★★（中）

**信じる理由**:
- 異なる指標を当てて生存数で判定したら、両者とも残った（YZ_vol は3層、CHOP は M15 のみ）
- 直感的に「振れ幅」と「方向性」は別軸に思える

**反証条件**:
- YZ_vol 高値領域 と CHOP 低値領域の重なりが大きい場合（例: 同一バーでの共起率が >40%）→ 直交ではなく、同じ現象を別角度から見ているだけ
- 「強トレンド = 高ボラ」の経験則が文献で実証されている場合（IRC: Bollen et al. の "trend volatility" 研究系）
- 合成（CHOP + YZ_vol M15 二層）が単独より TR を改善しない場合 → 二指標が独立に貢献していない傍証 = **Task #25 の本質的検証点**

**検証ステータス**: 未検証（共起率を測っていない / 合成 = Task #25 残）

**撤回時の連鎖**: SPEC_v2.md § 2-1 の M15 二層構造（CHOP 補完 + YZ_vol 補完）が破綻。中期 H1 / 長期 D1 が YZ_vol 単独前提なので影響は M15 限定。

**関連教訓**: `LESSON_2026-05-08_yz_vol_universal.md`（YZ_vol が3層全てで効いた）

**Step B で当たる文献の方向**:
- Choppiness Index (Bill Dreiss, 1990s) の原典と FX 応用
- Yang & Zhang (2000) original paper, OHLC volatility estimator
- "trend volatility correlation FX" "directional volatility orthogonality"
- Murphy "Technical Analysis of Financial Markets" trend vs volatility の章

---

## H3. M15 / H1 / D1 三層仮説

**主張**: 季節判定の三層は **M15 / H1 / D1** で必要十分。M5 / W1 / MN は不要。

**信じる強さ**: ★★（中）

**信じる理由**:
- 既存システムが M15 ループで動いている（実装の都合）
- D1 までで「気候帯」が捉えられそう（直感）
- Triple Screen (Elder) の3階層概念に類似（要照合）

**反証条件**:
- W1 や MN のレジームが M15 取引のリスク管理に有意な情報を与える文献的根拠がある場合
- M5 の超短期ボラ（マイクロストラクチャ）が M15 シグナル発火直前の濾過に効くことが示せる場合
- 三層の比率が等距離 (M15→H1=4倍, H1→D1=24倍) で偏っており、欠けた中間層 (例: H4) を入れると改善する場合

**検証ステータス**: 未検証（**三層の数と比率そのものを直接検証していない**）

**撤回時の連鎖**: 三層構造の前提が崩れると、SPEC_v2.md § 2-1 の各セルの**意味づけ**（短期/中期/長期）が再定義必要。閾値そのものは時間軸別に取得済みなので値は流用可能。

**関連教訓**: `LESSON_2026-05-07_indicator_timeframe_specificity.md`（指標は時間軸特異性を持つ — 三層が必要であることの傍証だが、なぜ M15/H1/D1 なのかは未論証）

**Step B で当たる文献の方向**:
- Elder "Trading for a Living" Triple Screen Trading System
- Pesavento & Jouflas マルチタイムフレーム分析
- "multi-timeframe analysis FX" "fractal market hypothesis"（Peters 1994）

---

## H4. ペア別閾値仮説

**主張**: USD_JPY / EUR_USD / GBP_JPY は**ペア別に閾値を分けるべき**である（一律閾値では不十分）。

**信じる強さ**: ★★★★（高）

**信じる理由**:
- 検証で各ペアの最適パーセンタイル位置が異なった（M15 YZ_vol で 30/80/30）
- PREMISE.md ノウハウ継承「ペア別の振る舞い違い」が一次仮説として明文化済み
- 実務的にも JPY クロス vs ドルストレート は性質が違うと広く言われる

**反証条件**:
- 一律閾値（3ペア共通の絶対値 or 共通パーセンタイル）と比較して、ペア別の TR 改善が誤差レベル（例: ΔTR < 0.05）の場合
- 文献で「FX ボラの絶対水準は通貨ペアによる差より時間帯による差が支配的」と示されている場合（要確認）

**検証ステータス**: 部分検証（ペア別最適値は導出済み、一律閾値との比較対照実験は**未実施**）

**撤回時の連鎖**: SPEC_v2.md § 2-1 の9セルが3セル（時間軸別共通閾値）に圧縮される。SPEC 全体構造への影響大。

**関連教訓**: なし（ペア別の差を所与としており、なぜその差が出るかの教訓化はされていない）

**Step B で当たる文献の方向**:
- BIS Triennial Survey での通貨ペア別ボラ統計
- Ito & Hashimoto JPY ボラの時間帯特性
- "currency pair volatility heterogeneity" "FX cross-section volatility"

---

## H5. TR > 1.0 合格基準仮説

**主張**: 自前定義の **Threshold Ratio (TR) が 1.0 を超える**ことを「指標が効いた」の最小ライン基準とする。IS_TR / OOS_TR ともに 1.0 超で採用候補、両方 1.5 超で強採用。

**信じる強さ**: ★★（中）

**信じる理由**:
- 1.0 = 「閾値で分けた両側で差がない（無情報）」のラインに見える
- IS と OOS の両方で 1.0 を超えるなら過適合は最低限抑制できそう

**反証条件**:
- TR の自前定義が文献の標準指標（profit factor, Sharpe ratio, hit rate ratio, AUC 等）に変換できない場合 → 比較不可能で議論が孤立
- Cross-validation や bootstrap で TR の標準誤差を求めると、1.0 と 1.05 の差が**統計的有意でない**と判明する場合
- 「1.5 超」の閾値が ad-hoc であり、サンプルサイズや時間軸によって正規化すべきだと示される場合

**検証ステータス**: 未検証（**TR の自前定義そのものの妥当性を文献用語で検証していない**）

**撤回時の連鎖**: SPEC_v2.md § 2-1 の全採用判定が再評価対象。値は再利用可能だが採用/不採用ラベルが変わる可能性。

**関連教訓**: `LESSON_2026-05-08_grid_granularity_and_length.md`（粗グリッドが偽 Spearman を生むという話 — TR の安定性とも関連）

**Step B で当たる文献の方向**:
- Bailey & López de Prado "The Deflated Sharpe Ratio" (2014)
- White "A Reality Check for Data Snooping" (2000)
- Romano & Wolf stepwise multiple testing
- Predictive vs Profitable の区別（Lo 2004 等）

---

## H6. 単一分割 walk-forward 仮説

**主張**: 単一の IS / OOS 分割で行った walk-forward 検証は、現段階の指標スクリーニングには**十分**である。

**信じる強さ**: ★（弱い — 後ろめたさあり）

**信じる理由**:
- 開発速度を優先した
- 単一分割でも「OOS で改善」が出れば嘘ではない（と思いたい）
- WFA の標準形式は知識として持っているが、実装コストを払っていない

**反証条件**:
- k-fold WFA や anchored / rolling window で TR の分散が大きい（例: 標準偏差が平均の30%超）と判明する場合
- 単一分割 OOS で採用された閾値が、別の分割では不採用になる場合
- 文献標準（Pardo 2008 等）が単一分割を「最低限以下」と扱っている場合

**検証ステータス**: 未検証（**単一分割の妥当性を多分割と比較していない**）

**撤回時の連鎖**: SPEC_v2.md § 2-1 の全数値が「再検証必要」マーク付きになる。値は無効化されないが信頼度が下がる。

**関連教訓**: なし

**Step B で当たる文献の方向**:
- Pardo "The Evaluation and Optimization of Trading Strategies" (2008) — WFA 標準形式
- "anchored walk-forward" "rolling walk-forward" "k-fold cross-validation time series"
- López de Prado "Advances in Financial Machine Learning" (2018) Combinatorial Purged Cross-Validation

---

## H7. 三層生存 = 採用根拠 仮説

**主張**: ある指標が **3つの時間軸（M15/H1/D1）全てで TR>1.0 を達成する**ことは、その指標を採用する**強い根拠**である。

**信じる強さ**: ★★★（中〜高）

**信じる理由**:
- 「複数時間軸で同じ現象が観察される」= フラクタル的安定性の傍証
- YZ_vol が3層全てで生存したのは偶然とは思いにくい
- LESSON_2026-05-08_yz_vol_universal.md で教訓化済み

**反証条件**（**ここが最も怖い**）:
- 三層生存が「過適合の兆候」と読める対立解釈が文献で支持されている場合 — つまり「**特定の指標を3つの時間軸で試して全部で動かしたグリッドサーチ自体**」が multiple testing problem の典型例として叩かれる場合
- 三層生存の検出力（power）を bootstrap で測ると、ランダム指標でも一定確率で達成すると判明する場合
- Yang-Zhang 推定量が「OHLC 情報を最大限使う設計」のため、**どんな時間軸でも数値的に安定する**だけで、レジーム情報を含んでいるわけではないと判明する場合

**検証ステータス**: 未検証（**ランダムベンチマークと比較していない** — これは致命的弱点）

**撤回時の連鎖**: SPEC_v2.md § 2-1 の YZ_vol 全層採用が崩れる。CHOP（M15のみ）の方が誠実な指標である可能性すらある。

**関連教訓**: `LESSON_2026-05-08_yz_vol_universal.md`（**この教訓自体が H7 を前提に書かれている** — 仮説と教訓が循環している危険）

**Step B で当たる文献の方向**:
- Sullivan, Timmermann, White "Data-Snooping, Technical Trading Rule Performance, and the Bootstrap" (1999)
- White Reality Check / Hansen SPA Test
- Harvey, Liu, Zhu "...and the Cross-Section of Expected Returns" (2016) multiple testing
- Bailey, Borwein, López de Prado, Zhu "Pseudo-Mathematics and Financial Charlatanism" (2014)

---

## H8. length grid {10,14,20,30} 妥当性仮説

**主張**: YZ_vol / CHOP の length パラメータの感度分析は **{10, 14, 20, 30} の4点**で実用十分である。

**信じる強さ**: ★★（中 — 後ろめたさあり）

**信じる理由**:
- 中央集中している（14 / 20 が中庸）
- 計算コストとの妥協
- 「飛び値で全部生存ならその間も大丈夫だろう」という滑らかさの仮定

**反証条件**:
- {12, 16, 18, 22, 24} など中間点で TR が崩れる場合（飛び値間の谷）
- length に対する TR が単峰形（unimodal）でなく多峰形（multimodal）と判明する場合 → 14 を引いたのは偶然
- 文献で他の length 値（例: 9, 21, 50 等のフィボナッチ系 / 19, 22 等の取引日系）が標準として採用されている場合

**検証ステータス**: 部分検証（4点で測ったがその間は補間で済ませている）

**撤回時の連鎖**: SPEC_v2.md § 2-1 の length 値（M15=14 / H1=20 / D1=20）が変更対象。値は再導出だが構造は不変。

**関連教訓**: `LESSON_2026-05-08_grid_granularity_and_length.md`（粗グリッドの罠 — D1 YZ_vol で経験済み。length grid もこの罠の対象）

**Step B で当たる文献の方向**:
- Wilder (1978) ATR の period=14 起源
- Yang & Zhang (2000) 推定量における window 長の理論的指針
- "moving window length selection" "periodicity in technical indicators"

---

## 仮説間の依存関係

```
H1 (3状態) ─┬─ H2 (直交分解) ─── Task #25 (合成検証)
            │
            └─ SPEC_v2.md § 2-1 全体

H3 (三層) ─── 三層一致スコアリング重み

H4 (ペア別) ── 9セル構造

H5 (TR>1.0) ─┬─ 全採用判定
H6 (単一WF) ─┘    の信頼度

H7 (三層生存) ── YZ_vol 全層採用 (★最も脆弱)
H8 (length 4点) ── length 確定値
```

**最も脆弱な仮説**: H7（ランダムベンチマーク未実施）と H6（多分割未実施）。両方とも検証コストは中程度で、回避すべき理由が「面倒」しかない。**Step C で文献を持ってきても、検証で当てる必要がある**。

**最も影響が大きい仮説**: H1（3状態モデル）。これが倒れると SPEC_v2.md § 2-1 の構造そのものが組み換え。

---

## 物語破棄オプション条項との接続

OPERATING_MODEL.md v2.1 巻末の「物語破棄オプション条項 (b)」は、postmortem が物語語彙で説明できない死因を続けた時に発火する。

**HYPOTHESES_2-1.md の同等条項**: H1〜H8 のうち**3つ以上が反証された場合**、本ドキュメント全体を `_archive/YYYY-MM-DD/HYPOTHESES_2-1.md` に移送し、SPEC_v2.md § 2-1 を**白紙から再起草**する。

これは「仮説の自己永続化バイアス」（書いた仮説に味方し続ける罠）への抗体である。

---

## 次のアクション

1. **本ドキュメントのレビュー**（庭師 — 仮説の追加・削除・強さ調整）
2. **Step B 起動**: researcher エージェント並列で各仮説の文献を収集（H1〜H8 ごとにキーワードと方向を上記に記載）
3. **Step C 三角測量**: 文献の期待値と自前検証結果を突き合わせ、SPEC_v2.md § 2-1 の根拠列を埋める

**SPEC v2 への影響予告**:
- Step B/C 完了時、SPEC_v2.md の各行に「文献根拠」列を追加する
- 反証された仮説に依存する SPEC 値は **取り消し線 + アーカイブ理由併記** で残す（消さない、年輪として保持）
