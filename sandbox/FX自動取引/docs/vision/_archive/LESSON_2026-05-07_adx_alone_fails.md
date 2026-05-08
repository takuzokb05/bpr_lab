# 教訓記録: ADX 単独でのレジーム判定は機能しなかった (2026-05-07)

> 運用モデル X-1「賢者の限界の自覚」の実例として、SPEC v2 の最初の検証で得た教訓を記録する。
> 物語上の意味: 賢者は「ADX>25 で trending」と長らく前提していたが、実証で**機能していなかった**ことを認めた。

## 状況

SPEC v2 で「2-1 季節判定の ADX trending 閾値」を最初の確定対象として選び、Walk-forward IS/OOS 検証を実施した。

- データ: MT5 M15、2年、3ペア (USD_JPY / EUR_USD / GBP_JPY)
- IS:OOS = 75:25
- ADX グリッド: [18, 20, 22, 25, 28, 30, 35]
- 評価関数: Trendiness Ratio (TR) + Directional Persistence Rate (DPR)
- スクリプト: `scripts/_spec_2_1_adx_threshold.py`

## 結果

| 指標 | 全ペア × 全閾値の範囲 | 意味 |
|---|---|---|
| **TR (Trendiness Ratio)** | 0.94 〜 1.12 | ADX>閾値でも値動きの大きさは ADX≤閾値とほぼ同じ（ratio≈1.0） |
| **DPR (Directional Persistence Rate)** | 0.45 〜 0.52 | ADX>閾値後の方向継続率はほぼ 0.5（ランダム水準） |
| **同等帯** | 18〜35 すべて | どの閾値も IS 最良の 90% 以内 = 統計的に区別不能 |

## 教訓

1. **ADX 単独でのレジーム判定は機能していない**。Wilder の rule of thumb (>25 で trending) は M15 の FX では実証されない
2. **既存実装の「ADX > 25」前提は脆弱**。PREMISE で「亡き者」化した正当性が実証された
3. **researcher 引用の "Rage Against the Regimes" 警告が実データで再現**: regime detection は PF に貢献しないという QuantConnect の主張は、少なくとも ADX 単独では正しい
4. **第一手の閾値選定で「指標そのものを疑う」結論に至った**ことは、SPEC 化作業が機能している証拠（数字を埋める作業の中で前提を疑える）

## 次のアクション

- 2-1 季節判定の指標構成を**再設計**（ADX + ATR + BBW + Hurst exponent + ボラ構造等の合成）
- ADX 単独の暫定 SPEC 値（>25）は記入したが、**「採用見送り推奨」を明記**
- 同様の手法で他の SPEC 項目を埋める際、**「単一指標の予測力ゼロ」リスクを最初に確認する**

## 物語的意味

賢者は「自信がないこと」を隠さず宣言する（X-1 の限界の自覚）。
このセッションで賢者は **「ADX>25」という長年の地図に従って動いていたが、実は地図が実態と一致していなかった**ことを認めた。
これは敗北ではなく、X-1 機能の最初の正常作動である。

---

**ファイル位置**: `docs/vision/_archive/LESSON_2026-05-07_adx_alone_fails.md`
**関連**:
- `data/spec_2_1_adx_summary.json` (生データ)
- `scripts/_spec_2_1_adx_threshold.py` (検証スクリプト)
- `docs/SPEC_v2.md` (2-1 季節判定の警告セクション)
- `docs/vision/OPERATING_MODEL.md` (X-1 限界の自覚)
