# プロポーザル: 適応的 ATR Breakout (signal_v2 改善版、レジーム別パラメータ + 動的 SL/TP)

## 1. 戦略仮説 (1段落)

撤退の決定打となった `signal_v2.py` (ATR breakout) は過去2年 PF 0.95 / シャープ -0.39 で失敗した (Pragmatist BT)。失敗の構造原因は **全レジーム一律で同じ ATR mult (SL 1.5 / TP 3.0)** を使ったこと。本提案はこの直接の改修で、**レジーム別に SL/TP mult を動的に切り替え** + **過去のブレイクアウト勝率に応じて発火閾値も適応** + **同方向のブレイクアウト連続失敗で自動停止** という 3層の改善で再挑戦する。「同じパラメータでもう一度走らせる」のではなく、「**亡き者の同じ仕様で過去2年 PF 0.95 だった事実から逆算して、何を変えれば PF>1.2 になるか**」をデータ駆動で設計する。

## 2. 想定エッジ源 [G1-1]

**構造的優位**:
- ブレイクアウト戦略自体は古典 (Donchian channel 1960s, Dennis & Eckhardt "Turtle Trading" 1983) で構造的優位が文献に厚い
- 失敗の原因は戦略思想ではなく**実装パラメータの硬直性**
- レジーム別パラメータは Lo (2004) "Adaptive Market Hypothesis" の現代的実装
- ATR スケーリングは Wilder (1978) からの古典的アプローチ

**実取引データの裏付け** ([[feedback-deceased-world-data-inheritance]] 遵守):
- 亡き者 signal_v2 BT: PF 0.95、累計 -385.8 pips (2年216件)
- スプレッドなし理論値: PF 1.01、+46.2 pips → **シグナル自体は break-even 付近、スプレッドで完全に死ぬ**
- 月別 PnL std 2,132 JPY (lot 0.01) で分散大 → ATR mult を**保守化すれば PnL の分散を縮められる**仮説
- 「同じ仕様で再挑戦してはいけない」が原則 ([[feedback-deceased-world-data-inheritance]]) → **本提案は同じではない**: 適応化 + レジーム認識 + 撤退ロジックの3点で別物

## 3. シグナル定義 (擬似コード)

```python
def generate_signal(data_m15, data_h1):
    # ステップ1: レジーム判定 (YZ_vol または ADX ベース)
    adx = ADX(data_m15, length=14)
    atr_pct = ATR(data_m15) / close * 100
    if adx > 30 and atr_pct > rolling_p70:
        regime = "STRONG_TREND"
    elif adx < 20:
        regime = "LOW_VOL"  # ブレイクアウト不利、HOLD
    else:
        regime = "NORMAL"

    if regime == "LOW_VOL":
        return HOLD  # ブレイクアウトはトレンド期だけ

    # ステップ2: 適応的ブレイクアウト閾値
    # 直近 30 trades の勝率から発火閾値を調整
    recent_win_rate = get_recent_win_rate(window=30)
    if recent_win_rate < 0.35:
        # 連敗中、閾値厳しく
        lookback = 30  # 通常 20
    else:
        lookback = 20

    high_n = data_m15.high.shift(1).rolling(lookback).max()
    low_n = data_m15.low.shift(1).rolling(lookback).min()
    atr = ATR(data_m15, length=14)

    # ステップ3: ブレイクアウト + レジーム別 SL/TP
    if close > high_n:
        if regime == "STRONG_TREND":
            sl_mult, tp_mult = 1.5, 3.0   # 大きく取りに行く
        else:  # NORMAL
            sl_mult, tp_mult = 1.2, 1.8   # 控えめ
        return BUY, atr, sl_mult, tp_mult

    if close < low_n:
        # 売りも同様
        ...

    return HOLD

# ステップ4: 連続失敗で自動停止
# 直近 5 trade が全て SL ヒットしたら、24時間取引停止
if last_5_all_SL():
    return HOLD  # cooldown
```

## 4. データ要件 [G1-2]

- MT5 EUR_USD/USD_JPY/GBP_JPY M15 + H1 (5年): 既存
- 過去 trade outcome の DB (recent_win_rate 計算用) — fx_trading.db で対応
- 追加 API 不要

## 5. リスクモデル [G1-5]

- SL: ATR × 1.2 (NORMAL) / 1.5 (STRONG_TREND) — 旧 signal_v2 の 1.5 固定より柔軟
- TP: SL距離 × 1.5 (NORMAL) / 2.0 (STRONG_TREND)
- 想定 MaxDD: -10% (旧 signal_v2 BT で -13,944 JPY/lot0.01 = -14% 相当を圧縮)
- テールリスク: 連敗で 24時間停止 (cooldown)
- ポジションサイジング: 口座 0.8% リスク (旧の 1% より保守化)

## 6. 自己改善メカニズム [G0-B] — 必須

**ドリフト検出 (毎日)**:
- 直近30日の勝率/PF/RR を計算
- 過去365日対比で win rate ±10% 変動でアラート
- ATR の絶対値が過去 90日対比で ±50% 変動でアラート (レジーム変化シグナル)

**パラメータ自動再最適化 (月次)**:
- lookback (15/20/30) × SL mult (1.0/1.2/1.5) × TP mult (1.5/2.0/2.5) × ADX threshold (20/25/30) のグリッド
- 直近 12ヶ月 IS / 3ヶ月 OOS WFA で評価
- 最良 OOS PF パラメータを採用 (各ペア独立に最適化)

**動的閾値 (連続的、再最適化不要)**:
- 直近 30 trade の win rate < 35% でブレイクアウト lookback を 30 (厳格化)
- win rate >= 50% で lookback を 15 (機会拡大)
- これは Phase 0 提案の中で唯一の **「BTやり直し不要の継続的自己改善」**

**フォールバック**:
- 新パラメータで 30日 PF<0.9 → 旧パラメータリバート
- 連続 5 trade SL ヒット → 24時間 cooldown
- 24時間 cooldown が月 2回以上発生 → 戦略停止 + Slack

**トリガー条件**:
- 毎日 06:00 JST ドリフトチェック
- 月初1日 全パラメータ再最適化
- 累計 -3,000 JPY / 90日 trades<20 / 月2回以上 cooldown → 撤退

## 7. 過去 BT 結果 [G0-A] — 必須

**現時点で示せる根拠**:
- 旧 signal_v2 BT: PF 0.95, 累計 -3,858 JPY (2年, lot 0.01, スプレッド込)
- 旧 signal_v2 スプレッドなし: PF 1.01
- 改善3点 (レジーム別 SL/TP + ADX フィルタ + cooldown) の効果は仮説段階

**Phase 1 で行うべき追加 BT (宿題)**:
- 改善版 signal_v2 を GBP_JPY/EUR_USD/USD_JPY M15 5年 で BT
- 期待値: 改善前 PF 0.95 → 改善後 PF 1.2 以上
- もし改善しても PF<1.0 のままなら→ **本提案は廃案** (ブレイクアウト自体が現代市場で機能していない結論)

**PF > 0.95 達成根拠**:
- 旧 PF 0.95 を超えること自体が改善目標 → BT 結果次第
- **G0-A の答えは「BT 次第」** であり、その意味では本提案は他の候補より弱い
- ただしブレイクアウト系には文献の蓄積がある (Turtle 流 Donchian 等で PF 1.3-1.5 報告例あり) ので、機能する可能性は残る

## 8. WFA / OOS [G1-7]

- 3-pair × 5-fold anchored expanding WFA = 計15 OOS 評価
- Deflated Sharpe (試行数: lookback 3 × SL 3 × TP 3 × ADX 3 = 81)
- IS と OOS の PF gap が ±0.3 以内であることを必須

## 9. 実装複雑度 [G1-3]

- 旧 `src/spec_v2/signal_v2.py` ロジックを流用 (パラメータ化可能な構造に書き直し)
- レジーム判定 ~50行
- 動的 lookback ~30行
- cooldown ロジック ~40行
- 自己改善モジュール ~250行
- **総工数: 2-3 週間**

## 10. 機会費用比較 [G1-6]

| 運用先 | 1年累計 (100万円口座) |
|---|---:|
| 銀行預金 | +500 JPY |
| 米国債 | +40,000 JPY |
| 旧 signal_v2 (PF 0.95, 実証) | **-19,290 JPY (毀損)** |
| 本提案 worst (PF 0.95 のまま) | 旧と同じ毀損 |
| 本提案 (PF 1.2 達成) | **+80,000 JPY** |
| 本提案 best (PF 1.4 達成) | **+150,000 JPY** |

## 11. リスク・既知の弱点

1. **同じ轍を踏むリスク**: 「亡き者で失敗した signal_v2 の改修」という構造そのものが [[feedback-deceased-world-data-inheritance]] 警告に該当。「BT で勝てたら採用」が約束されないなら廃案
2. **過剰最適化リスク**: グリッド試行数 81 で Deflated Sharpe が大きく落ちる可能性
3. **ブレイクアウト自体が死んでいる可能性**: 2020s 中盤の市場ではアルゴ集中で「ブレイクアウト騙し」が増えた可能性 (検証要)
4. **レジーム判定の遅延**: ADX は遅行指標で、判定が遅れると既に機会を逃している
5. **cooldown の罠**: 連敗→停止→相場転換で「最も儲かるタイミング」を逃す
6. **動的閾値の自己関与**: 連敗中に厳格化すると trade 数が減り、評価不能の罠

## 12. 採点自己評価

| Gate | 項目 | 自己採点 | 根拠 |
|---|---|---:|---|
| G0-A | PF > 0.95 | **CONDITIONAL** | 改善版BT次第。改善が効かなければ廃案。事前根拠は弱い |
| G0-B | 自己改善 | **PASS** | 動的閾値 (連続的) + 月次再最適化 + cooldown + フォールバック多層 |
| G1-1 | エッジ源 | **6/10** | ブレイクアウトは文献厚いが、亡き者で失敗実証あり |
| G1-2 | データ要件 | **10/10** | 既存 |
| G1-3 | 実装複雑度 | **6/10** | 旧コード流用可、3週間 |
| G1-4 | ロバスト性 | **5/10** | 多パラメータで過剰最適化リスク高 |
| G1-5 | リスク | **7/10** | cooldown / リバート / 撤退ライン明確 |
| G1-6 | 機会費用 | **7/10** | BT で機能すれば +8〜15万、worst で毀損 |
| G1-7 | WFA/OOS | **5/10** | 試行数 81 で Deflated Sharpe 厳しい |
| G2-1 | スプレッド耐性 | **2/5** | 旧 BT で「スプレッドだけで死ぬ」と実証、最大の弱点 |
| G2-2 | 相関 | **5/5** | 平均回帰系と完全に逆相関、ポートフォリオ分散源として価値 |
| G2-3 | 説明可能性 | **5/5** | ブレイクアウト + ATR は人間が後追い可能 |
| G2-4 | レビュー耐性 | **2/5** | 「亡き者の失敗を改修」は karen/Pragmatist 批判直撃 |
| G2-5 | 拡張性 | **4/5** | ペア追加・タイムフレーム変更が容易 |
| G2-6 | 過去挙動整合 | **2/5** | 亡き者で完全に負けたパターンを継承、整合性が逆に弱点 |

**Gate 0**: G0-B PASS、**G0-A は CONDITIONAL** (BT結果次第)
**Gate 1 合計**: 46/70
**Gate 2 合計**: 20/30
**総合**: **66/100** — Phase 2 進出は微妙、BT 結果を見てから判断

## 撤退条件 (先に書く)

- Phase 1 BT で PF<1.0 → 即廃案 (Phase 2 進出せず)
- 90日経過時点で trades<20 → 撤退
- 90日経過時点で PF<1.0 → 撤退
- 累計 PnL<-3,000 JPY → 即撤退
- 月2回以上 cooldown 発動 → 戦略停止

## 提案者注記

本提案は **「亡き者で負けた仕様の改修」** という [[feedback-deceased-world-data-inheritance]] 警告に最も近い。**Phase 1 BT で PF 1.2 が出なければ即廃案** が前提。出した理由は「ブレイクアウト系は分散源として価値があり、もし改善で機能するなら他候補と低相関なポートフォリオ要素になる」点。
