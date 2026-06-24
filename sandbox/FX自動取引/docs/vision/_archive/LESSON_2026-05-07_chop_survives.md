# 教訓記録: Choppiness Index が ADX 代替として全ペア生存 (2026-05-07)

> 運用モデル X-1「賢者の限界の自覚」と対をなす **「賢者が学んだ瞬間」** の記録。
> ADX 単独失敗の数時間後に、6指標スクリーニングで CHOP が確かな代替候補として浮上した。

## 経緯

ADX 単独の失敗を受けて、6領域並列リサーチ（A 学術 / B ML / C 業界 / D マイクロ / E 合成 / F 既存知見）を実施。
ロングリスト13候補 → ショートリスト6指標 → スクリーニング実施。

スクリプト: `scripts/_spec_2_1_indicator_screening.py`
データ: `data/spec_2_1_indicator_screening.json`

## 結果

### 生存指標（IS_TR>1.05 AND OOS_TR>1.0 AND max(Spearman)>0.5）

| 指標 | USD_JPY | EUR_USD | GBP_JPY | 生存率 |
|---|:-:|:-:|:-:|:-:|
| **CHOP (Choppiness Index)** | ✓ | ✓ | ✓ | **3/3** |
| YZ vol (Yang-Zhang) | ✗ | ✓ | ✓ | 2/3 |
| Range/ATR | ✓ | ✗ | ✓ | 2/3 |
| Hurst | ✗ | ✗ | ✗ | 0/3 |
| VR (Variance Ratio) | ✗ | ✗ | ✗ | 0/3 |
| MFI | ✗ | ✗ | ✗ | 0/3 |

### CHOP の最強数値

- USD_JPY: best_thr<35, IS_TR=1.085, OOS_TR=**1.197**（OOS で改善）, Spearman_TR=+0.543
- EUR_USD: best_thr<30, IS_TR=1.182, OOS_TR=1.206, Spearman_TR=+0.600
- GBP_JPY: best_thr<30, IS_TR=1.254, OOS_TR=1.263, Spearman_TR=+0.543

## なぜ CHOP は効いて ADX は効かなかったか（仮説）

- **ADX**: True Range の Smoothed Average → **方向性の強さ**を測る
- **CHOP**: log10(ΣATR / 価格レンジ) → **動きの効率性**（直線的か、ジグザグか）を測る

M15 FX のノイズ環境では「方向性が出ている」より「**効率的に動いているか**」の方がレジーム判定に効く、という実証的発見。

## 教訓

1. **「指標が効かない」≠「レジーム判定が無理」** — ADX が機能しないからレジーム判定全体が無理という結論には至らなかった
2. **6領域並列リサーチが機能した** — 各領域から異なる指標が出て、スクリーニングで自然に絞り込めた
3. **既存資産の TR/DPR フレームが鍵** — ADX 検証で構築したフレームを 6指標で再利用できた（領域F の発見の通り）
4. **「合成すれば良くなる」幻想に乗らなかった** — 領域E の警告（noise を足しても noise）を踏まえ、まず単独で IC>0 を確認する戦略が功を奏した
5. **3指標が生存** — CHOP 単独で十分だが、合成検証で更なる向上の余地あり

## 次のアクション

- ✅ SPEC v2 の 2-1 を CHOP 主指標で更新（ペア別閾値）
- ⏭ Task #25: CHOP + YZ_vol + Range_ATR の合成検証
- ⏭ length=14 以外の感度分析（CHOP 計算期間）
- ⏭ 物語破棄オプション条項の発火条件 (b)「物語の語彙では説明できない死因」のテストケースとして本セッションを記録

## 物語的意味

ADX 単独失敗の教訓記録（`LESSON_2026-05-07_adx_alone_fails.md`）に対する**続編**。
庭師と賢者は「ADX という地図が間違っていた」を認め、6領域の地図を改めて広げ、
**Choppiness Index という新しい地図**を見つけた。これが「自己改善する至高のFXストラテジ」の最初の真の自己改善である。

---

**ファイル位置**: `docs/vision/_archive/LESSON_2026-05-07_chop_survives.md`
**関連**:
- `LESSON_2026-05-07_adx_alone_fails.md` (前段)
- `data/spec_2_1_indicator_screening.json` (生データ)
- `scripts/_spec_2_1_indicator_screening.py` (検証スクリプト)
- `docs/SPEC_v2.md` (CHOP 主指標で更新済み)
- `docs/vision/OPERATING_MODEL.md` (X-1 限界の自覚 + 自己改善の実例)
