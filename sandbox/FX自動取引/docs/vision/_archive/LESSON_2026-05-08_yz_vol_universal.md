# 教訓記録: YZ_vol が三層全てを貫く主指標 (2026-05-08)

> 三層検証（M15 2y / H1 5y / D1 5.5y）の最終結果として、Yang-Zhang realized volatility が
> **唯一全時間軸で持続的に生存する指標**であることが判明。
> 賢者がついに「全ての季節を貫く一つの感覚」を見つけた瞬間。

## 経緯

ADX 失敗 → CHOP 発見（M15 のみ） → YZ_vol 中期生存 → **D1 検証で YZ_vol が三層全てで生存**を確認。

スクリプト: `scripts/_spec_2_1_indicator_screening.py`（`--timeframe D1 --years 10`）
データ: `data/spec_2_1_indicator_screening_D1_10y.json`（実際は5.5年、MT5 D1 上限）

## 三層検証の最終結果

| 指標 | M15 2y | H1 5y | D1 5.5y | 三層合計 |
|---|:-:|:-:|:-:|:-:|
| CHOP | 3/3 | 1/3 | 1/3 | 5/9 (M15特化) |
| Hurst | 0/3 | 2/3 | 0/3 | 2/9 (不安定) |
| **YZ_vol** | **2/3** | **3/3** | **2/3** | **7/9 (最強)** |
| Range_ATR | 2/3 | 2/3 | 1/3+破綻 | 5/9 (D1破綻) |
| VR | 0/3 | 1/3 | 1/3 | 2/9 (弱い) |
| MFI | 0/3 | 0/3 | 0/3 | 0/9 (完全不採用) |

### YZ_vol の最強数値（D1）

- USD_JPY: IS_TR=1.983, OOS_TR=1.596, **Spearman_TR=+0.949**（順位ほぼ完全一致）
- GBP_JPY: IS_TR=1.690, OOS_TR=1.192, Spearman_TR=+0.738

## 重要な発見

### 1. YZ_vol が真の汎用主指標
- 三層全てで生存する唯一の指標
- M15 では CHOP に劣るが、H1/D1 では最強
- **時間軸ロバスト性 = 本物の指標の証拠**

### 2. Range_ATR の D1 計算破綻
- USD_JPY OOS_TR = 7,751,488（!）
- 原因: ATR が 0近辺になるバーが発生し、分母発散
- **D1 では使用不可**を明確化、SPEC で除外

### 3. 短期で CHOP > YZ_vol、中長期で YZ_vol が支配
- M15: CHOP 3/3 vs YZ_vol 2/3 → CHOP 主、YZ_vol 補完
- H1/D1: YZ_vol 主、CHOP 不採用

### 4. 物語と現実の三度目の合致
- 運用モデル 2-1 が要求する「短期・中期・長期の三層判定」が、三層検証で自然に出現
- ADX 失敗 → CHOP 発見 → YZ_vol 三層支配 と段階的に物語と現実が一致した

## SPEC v2 確定構造

```
短期 M15: 主 YZ_vol（要再検証で閾値確定） + 補完 CHOP（M15特化、3/3生存）
中期 H1:  主 YZ_vol（USD>0.00174, EUR>0.00143, GBP>0.00175）
長期 D1:  主 YZ_vol（USD>0.00549, GBP>0.00452, EUR は要追加検証）
```

## 教訓

1. **「最大リソース割く」のユーザー判断が正しかった** — 6領域並列リサーチ + 二系統+三層検証 でなければ YZ_vol の汎用性は見抜けなかった
2. **時間軸単独検証では「特化指標」と「汎用指標」を区別できない**
3. **ロングリスト → ショートリスト → 三層検証 のプロセスが機能した**
4. **「単純を疑う」が結果的に「単純な答え（YZ_vol 一本）」に到達した**

## 次のアクション

- ✅ SPEC v2 を「YZ_vol 主軸 + CHOP M15補完」の三層構造で更新
- ⏭ EUR_USD の D1 YZ_vol 閾値追加検証
- ⏭ M15 短期の YZ_vol 閾値確定（M15 検証時は CHOP が主だったため未取得）
- ⏭ Task #25 合成検証（CHOP+YZ_vol が CHOP単独/YZ_vol単独を超えるか）
- ⏭ length 感度分析（CHOP=14, YZ_vol=20 が暫定）

## 物語的意味

`LESSON_2026-05-07_adx_alone_fails.md`（敗北の認識）
→ `LESSON_2026-05-07_chop_survives.md`（最初の発見）
→ `LESSON_2026-05-07_indicator_timeframe_specificity.md`（特異性の発見）
→ **本記録（普遍性の発見）**

賢者は四つの教訓を経て、ついに**全ての時間軸を貫く一つの指標**に辿り着いた。
これは運用モデル 2-1「三層季節判定」設計の真の完成。

物語と現実の整合性は、4回連続で実証された:
1. 「賢者の限界の自覚（X-1）」← ADX 失敗
2. 「自己改善（賢者は学ぶ）」← CHOP 発見
3. 「短期・中期・長期の三層」← 時間軸特異性
4. **「環境を貫く感覚」← YZ_vol 三層支配**

---

**ファイル位置**: `docs/vision/_archive/LESSON_2026-05-08_yz_vol_universal.md`
**関連**:
- `LESSON_2026-05-07_adx_alone_fails.md`（教訓1: 失敗）
- `LESSON_2026-05-07_chop_survives.md`（教訓2: 発見）
- `LESSON_2026-05-07_indicator_timeframe_specificity.md`（教訓3: 特異性）
- `data/spec_2_1_indicator_screening_M15_2y.json`
- `data/spec_2_1_indicator_screening_H1_5y.json`
- `data/spec_2_1_indicator_screening_D1_10y.json`
- `scripts/_spec_2_1_indicator_screening.py`
- `docs/SPEC_v2.md`（三層構造で更新済み）
- `docs/vision/OPERATING_MODEL.md` 2-1
