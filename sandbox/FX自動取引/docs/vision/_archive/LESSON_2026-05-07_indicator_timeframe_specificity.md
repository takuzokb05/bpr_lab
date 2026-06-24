# 教訓記録: 指標は時間軸スケール特異性を持つ (2026-05-07)

> ADX 単独失敗 → CHOP 発見 → さらに二系統検証で「**指標は時間軸を変えると性能が逆転する**」ことを実証。
> researcher 領域 A の警告「時間軸ごとに独立に walk-forward すること」が実データで再現された。

## 経緯

CHOP が M15 2年で全ペア生存した結果を踏まえ、ユーザーが「2年は短い、他のデータソースは?」と問題提起。
MT5 H1 5年で再検証する二系統アプローチを採用。

スクリプト: `scripts/_spec_2_1_indicator_screening.py`（`--timeframe H1 --years 5` で実行）
データ: `data/spec_2_1_indicator_screening_H1_5y.json`

## 結果（M15 2y vs H1 5y）

| 指標 | M15 2y 生存率 | H1 5y 生存率 | 解釈 |
|---|:-:|:-:|---|
| **CHOP** | **3/3** | **1/3** | **時間軸特異**（M15専用） |
| Hurst | 0/3 | 2/3 | H1 で出現 |
| **YZ_vol** | 2/3 | **3/3** | **時間軸ロバスト** |
| Range_ATR | 2/3 | 2/3 | 同等（ペアは違う） |
| VR | 0/3 | 1/3 | やや改善 |
| MFI | 0/3 | 0/3 | 不採用確定 |

### CHOP の H1 5y での崩壊

- USD_JPY: IS_TR=1.144 OOS_TR=1.003（ギリギリ）, Spearman_TR=**-0.829**（**完全な順位逆転**）
- EUR_USD: OOS_TR=0.881（OOSで負け）
- GBP_JPY: Spearman_TR=-0.143（順位無相関）

→ M15 で効いていた CHOP の閾値順位が H1 ではほぼ反転。**M15 短期スケール特異な現象**。

### YZ_vol の H1 5y での強さ

- USD_JPY: IS_TR=2.016, OOS_TR=1.916, Spearman_TR=+0.800（最強）
- EUR_USD: IS_TR=1.772, OOS_TR=**1.922**（OOSで改善）, Spearman_TR=+0.800
- GBP_JPY: IS_TR=1.776, OOS_TR=**2.031**（OOSで改善）, Spearman_TR=+0.400 / DPR=+0.800

IS_TR ~ 2.0 は CHOP M15 の 1.1 を**倍以上**上回る。

## 教訓

### 1. 指標は時間軸特異性を持つ
- 同じ価格データから計算しても、時間軸スケールが違えば指標の予測力は変わる
- M15 で効く指標（CHOP）が H1 で効くとは限らず、逆もまた然り
- researcher 領域 A の警告「時間軸を変えると ADX 分布が変わる。閾値は時間軸ごとに独立に walk-forward すること」が実データで再現された

### 2. 二系統検証の真の価値
- M15 単体検証では見抜けなかった「時間軸特異性」を H1 検証で発見できた
- ユーザーの「他に落ちてないのかね」「2年は短い」という問題提起が直接 SPEC の質を上げた

### 3. 「単独で生存」≠「普遍的に強い」
- CHOP M15 は OOS_TR が IS_TR を上回る再現性を示した（過剰最適化ではない）
- が、時間軸を変えると別の話になる
- **採用する時は「適用条件（時間軸範囲）」を明示する必要**

### 4. YZ_vol が真の主指標候補
- M15 2年で 2/3 / H1 5年で 3/3 = 時間軸ロバスト
- IS_TR ~ 2.0 という強い数値
- 長期データで COVID/利上げ/円安の異なるレジームを含めて生存

## 次のアクション

- ✅ SPEC v2 の 2-1 を「短期 CHOP / 中期 YZ_vol の二層構造」に更新
- ⏭ 長期（D1 等）指標の決定 — 別タスク
- ⏭ 合成検証（CHOP + YZ_vol + 他） — Task #25
- ⏭ length 感度分析（CHOP=14, YZ=20 が暫定値） — 別タスク

## 物語的意味

`LESSON_2026-05-07_adx_alone_fails.md`（敗北）→ `LESSON_2026-05-07_chop_survives.md`（最初の発見）→ 本記録（**より深い発見**）

賢者は「ADX が間違っていた」ことを認め（X-1 限界の自覚）、新地図 CHOP を見つけ（自己改善）、さらに「**地図はスケールごとに違う必要がある**」ことを学んだ。これは運用モデル 2-1「短期・中期・長期の三層」設計の必然性を実証する瞬間。

物語と現実の整合性が**逆方向に**も働いた: 物語が要求していた「三層判定」が、検証データから自然に出てきた。

---

**ファイル位置**: `docs/vision/_archive/LESSON_2026-05-07_indicator_timeframe_specificity.md`
**関連**:
- `LESSON_2026-05-07_adx_alone_fails.md`（前段1: ADX 失敗）
- `LESSON_2026-05-07_chop_survives.md`（前段2: CHOP 発見）
- `data/spec_2_1_indicator_screening_M15_2y.json` (M15 結果)
- `data/spec_2_1_indicator_screening_H1_5y.json` (H1 結果)
- `scripts/_spec_2_1_indicator_screening.py` (検証スクリプト、`--timeframe` 引数で切替可能)
- `docs/SPEC_v2.md` (二層構造で更新済み)
- `docs/vision/OPERATING_MODEL.md` 2-1（三層判定の設計と整合）
