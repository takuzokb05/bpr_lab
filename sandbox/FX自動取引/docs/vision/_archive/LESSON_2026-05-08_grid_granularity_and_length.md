# 教訓記録: 粗グリッドの偽 Spearman と length パラメータの決定的影響 (2026-05-08)

> 三層検証完了後の SPEC v2 穴埋め作業 (A-1/A-2/A-3) で発見した、**「指標が効くかどうかは閾値だけでなく、グリッド粒度と length パラメータの組合せで決まる」**という運用上極めて重要な学び。

## 経緯

YZ_vol が三層全てで主指標と確定（前 lesson）した後、SPEC v2 の閾値穴埋めを実施。
- A-1: D1 EUR_USD 閾値追加検証
- A-2: M15 YZ_vol 閾値確定
- A-3: window/length 感度分析

データ:
- `data/spec_2_1_yz_vol_revalidation_D1_10y.json`
- `data/spec_2_1_yz_vol_revalidation_M15_2y.json`
- `data/spec_2_1_length_sensitivity.json`

## 発見

### 1. 粗グリッドは偽の Spearman 順位相関を生む

D1 USD_JPY YZ_vol の Spearman_TR:
- **粗 4点グリッド** (25/50/75/90%ile): **+0.949**（順位ほぼ完全一致）
- **細 9点グリッド** (30/40/50/55/60/65/70/75/80%ile): **+0.050**（ほぼ無相関）

これは粗グリッドの閾値間ジャンプ（IS_TR が 1.68→1.98→1.68→1.54 と単調でない動き）が偶然 OOS の動きと一致して見えるための擬似相関。細グリッドにすると IS_TR がフラット (1.66-1.98 の狭範囲) なのが見える → **「閾値選択の意味がない」が本当の姿**。

ただし TR 絶対値は IS/OOS とも全閾値で >1.0 → 「広域有効・閾値感度低」型 robust 指標と再認識。

### 2. length パラメータが指標生死を決める（決定的事例）

**M15 USD_JPY YZ_vol**:
- window=20 → Spearman_TR=-0.833（順位反転）→ 一旦「不採用」と判断
- window=14 → IS_TR=1.461, OOS_TR=1.138 → **採用可**（USD_JPY M15 でも YZ_vol が機能する）

window=14 と window=20 はわずか 6 バー差。なのに「死」と「生存」を分ける。

**全感度分析 (3時間軸 × 3ペア × 4window = 36通り)**:
- 36/36 全てが best_eligible 採用可
- ただし最適 window はペア・時間軸で変動
- 時間軸別最適: **M15=14 / H1=20 / D1=20**

### 3. 「閾値最適化」より「length 最適化」が先

M15 YZ_vol の例:
- window=20 で Spearman_TR=-0.833 を見ると、誰しも「指標が効かない」と判断したくなる
- しかし真因は「window 選択ミス」
- window=14 にすると同じ閾値範囲で順位相関も予測力も成立

**閾値が効かない時、まず length を疑え**。これは将来の指標検証で必ず確認すべき手順。

## 教訓

### 1. グリッド粒度は最低 7-9 点必要
- 4点だと閾値間ジャンプが偽相関を作る
- 7点以上で閾値の真の感度（フラット vs 単調 vs 反転）が見える
- Spearman 順位相関は「グリッド粒度」と「IS_TR の閾値分散」両方に強く依存する

### 2. length 感度分析は閾値検証と同等に重要
- 暫定 length（pandas-ta デフォルト等）で「効かない」と判断するのは早計
- 最低 4 length 値でスクリーニングして、length-閾値マトリクスで「広域生存」を確認
- length は時間軸特異性を持つ可能性があるので、時間軸ごとに最適化

### 3. Spearman 反転は length 不適合のサイン
- 閾値が高くなるほど OOS_TR が低くなる現象（IS と逆）は length が長すぎる証拠の可能性
- 短い length に変えると順位が IS と整合することが多い
- これは指標の周期性と価格動きの周期性のミスマッチを示唆

### 4. 「広域有効・閾値感度低」型指標の存在
- 全閾値で OOS_TR>1.0 が成立するが Spearman は低い
- これは「閾値最適化に意味なし、運用ではどの閾値でも効く robust 指標」
- 過剰最適化リスクが小さい良い指標
- D1 YZ_vol が典型例（USD_JPY/EUR_USD）

## SPEC v2 への反映

「2-1 季節判定」セクションが完全に閾値・パラメータ確定:

```
短期 M15:
  主 CHOP (length=14, < 35/30/30 ペア別)
  補完 YZ_vol (window=14, > 0.00038/0.00054/0.00039 ペア別)

中期 H1:
  主 YZ_vol (window=20, > 0.00174/0.00143/0.00175 ペア別)

長期 D1:
  主 YZ_vol (window=20, > 0.00549/0.00537/0.00570 ペア別)
```

## 次のアクション

- ⏭ Task #25: CHOP+YZ_vol 合成検証（M15 で二層補完が単独を超えるか）
- ⏭ 季節判定の三層一致スコアリング重み設計（短期 CHOP+YZ / 中期 YZ / 長期 YZ）
- ⏭ SPEC v2 「2-2 異常気象警報」着手

## 物語的意味

本 lesson は「賢者は更に深く学ぶ」段階の記録:

1. `LESSON_2026-05-07_adx_alone_fails.md`（敗北の認識）
2. `LESSON_2026-05-07_chop_survives.md`（最初の発見）
3. `LESSON_2026-05-07_indicator_timeframe_specificity.md`（特異性の発見）
4. `LESSON_2026-05-08_yz_vol_universal.md`（普遍性の発見）
5. **本記録（道具の使い方の発見）**

四つの教訓で「何を使うか」を学んだ賢者が、五つ目で「**どう使うか**」を学んだ瞬間。指標自体の選択以上に、その**測り方（グリッド粒度）と組み立て方（length）**が運命を決める。

物語と現実の整合性は5度目の合致:
- 「環境を貫く感覚を持つ」← YZ_vol 三層支配（前回）
- 「**感覚の使い方を磨く**」← 本記録、grid 細粒化と length 適合化

---

**ファイル位置**: `docs/vision/_archive/LESSON_2026-05-08_grid_granularity_and_length.md`
**関連**:
- `LESSON_2026-05-08_yz_vol_universal.md`（前段: 普遍性の発見）
- `data/spec_2_1_yz_vol_revalidation_D1_10y.json`
- `data/spec_2_1_yz_vol_revalidation_M15_2y.json`
- `data/spec_2_1_length_sensitivity.json`
- `scripts/_spec_2_1_d1_yz_vol_revalidation.py`（細グリッド + サンプル考慮型 revalidation）
- `scripts/_spec_2_1_length_sensitivity.py`（length 感度分析）
- `docs/SPEC_v2.md`（2-1 季節判定 完全閾値確定）
