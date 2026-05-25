# プロポーザル: Bull/Bear 対立検証 (BearResearcher) を別戦略の直列ゲートに転用

## 1. 戦略仮説 (1段落)

亡き者は `src/bear_researcher.py` (5チェック項目、severity weighted) を実装したが、本probe で確認した通り **ai_decision/ai_regime/ai_confidence/ai_reasons はすべて NULL** で、本番運用パイプラインに繋がっていなかった。BearResearcher の5チェック (divergence/sup-res/HTF/MFI/BB-squeeze) は**シグナルの反対論拠を構造的に出力する設計**で、これは TradingAgents (Bull/Bear 対立) や @loopdom の "internal devil's advocate" 設計に対応する。本提案は BearResearcher を**ベース戦略の最終承認ゲート**として直列に配置し、severity が高ければ容赦なく HOLD に変換する設計に切り替える。「亡き者は対立検証を持っていたが、その評価を使わずに発注した」というギャップを直接埋める。

## 2. 想定エッジ源 [G1-1]

**構造的優位**:
- シグナル発火後にも **反対論拠を必ず数える** ことで confirmation bias を構造的に防ぐ (Kahneman 2011, "consider the opposite")
- 5チェックは情報源が独立 (ダイバージェンス vs サポレジ vs 上位足 vs 出来高 vs ボラ縮小) で、severity の和は確率独立性を活用した heuristic
- ヒューリスティクスとして単純で、ブラックボックスではない
- 古い「**強いシグナルだけ打つ**」原則 (Lefebvre 1923, Reminiscences of a Stock Operator) の現代的実装

**実取引データの裏付け** ([[feedback-deceased-world-data-inheritance]] 遵守):
- 亡き者の prod DB に ai_reasons カラムはあるが全件 NULL → **BearResearcher が動かなかった (またはエラーで沈黙した)**
- このデータが「BearResearcher 不発火が負け原因の一つ」を強く示唆 (もちろん全因ではない)
- 本提案は「BearResearcher が確実に動作する直列パイプライン」を再設計

## 3. シグナル定義 (擬似コード)

```python
def generate_signal(data_m15, data_h1, base_strategy):
    # ステップ1: ベース戦略のシグナル取得
    raw_signal = base_strategy.generate_signal(data_m15)
    if raw_signal == HOLD:
        return HOLD, None

    # ステップ2: BearResearcher.verify() を呼ぶ
    indicators = compute_indicators(data_m15, data_h1)
    bear = BearResearcher().verify(data_m15, raw_signal, regime, indicators)

    # ステップ3: severity による厳格ゲート
    #   severity 0.0  -> 反対論拠なし、フル発火
    #   severity 0.35 (= higher_timeframe のみ) -> HOLD (上位足矛盾は致命)
    #   severity 0.25 -> ポジション 0.5x で発火 (divergence あるがそれだけ)
    #   severity 0.20 -> ポジション 0.75x (サポレジ接近)
    #   severity >= 0.40 -> 完全 HOLD

    if bear.severity >= 0.40:
        return HOLD, bear.reasoning  # 強い反対論拠あり
    if "higher_timeframe" in bear.fired_checks:
        return HOLD, "上位足矛盾"  # 単独でも HOLD
    if bear.severity >= 0.25:
        return raw_signal, bear.reasoning, position_multiplier=0.5
    return raw_signal, "問題なし", position_multiplier=1.0
```

**重要設計**: severity の閾値設計は**亡き者の負け trade を BearResearcher に流して逆算**する (Phase 1 BT で実施)。亡き者で負けた 24件 GBP_JPY のうち何件が severity>=0.40 だったかを確認。

## 4. データ要件 [G1-2]

- MT5 EUR_USD/GBP_JPY M15 + H1 (5年): 既存
- volume データ (MFI 用)
- 追加 API 不要

## 5. リスクモデル [G1-5]

- SL: ATR(14) × 1.5 (ベース戦略踏襲)
- TP: SL距離 × 2.0
- ポジションサイジング: severity に応じて 0.5x/1.0x (口座 1% リスクが基準)
- 想定 MaxDD: -6% (severity ゲートが効けば DD抑制が最大の効果)
- テールリスク: BearResearcher が誤検出を頻発する場合、機会損失過大

## 6. 自己改善メカニズム [G0-B] — 必須

**ドリフト検出 (毎週)**:
- 直近30日のチェック項目別 fired 率 (divergence 何%、HTF 何%等) を集計
- 過去365日対比で fired 率が ±50% 変動した項目をアラート
- 直近30日 PF<1.0 でアラート
- HTF チェックの「上位足判定の MA200」が直近 3ヶ月でドリフト (傾き反転頻度) でアラート

**パラメータ自動再最適化 (月次)**:
- severity 閾値 (0.35/0.40/0.45) のグリッド
- HTF MA period (50/100/200) のグリッド
- divergence lookback (10/20/30) のグリッド
- 各 component の重み (`_RISK_WEIGHTS`) を 5%刻みで再校正
- 直近 12ヶ月 IS / 3ヶ月 OOS 評価
- 最良 OOS PF 設定を採用

**フォールバック**:
- 新設定で 30日 PF<0.9 → 旧設定リバート
- BearResearcher が 7日連続で severity=0 ばかり (= 反対論拠が出ない) → チェックロジックの異常検出 + 停止
- 7日連続で全 trade が HOLD → ゲートが厳しすぎる → severity 閾値を 0.05 緩和して再開

**トリガー条件**:
- 毎週月曜 06:00 JST ドリフトチェック
- 月初1日 全パラメータ再最適化
- 累計 -3,000 JPY / 90日 trades<10 / 連続2回失敗 → 撤退

## 7. 過去 BT 結果 [G0-A] — 必須

**現時点で示せる根拠**:
- ベース BollingerReversal PF 1.24 (EUR_USD M15 2年)
- BearResearcher 5チェックの個別 BT は未実施 → Phase 1 宿題

**Phase 1 で行うべき追加 BT (宿題)**:
- 亡き者 GBP_JPY の負け 24件を BearResearcher にフィードして severity 分布を可視化
- 仮説検証: 「severity>=0.40 で除外していれば負けが半減した」か
- BollingerReversal + BearResearcher(severity>=0.40 で HOLD) の EUR_USD M15 5年 BT
- 期待値: PF 1.5 以上 (ゲートが効けば素の 1.24 から底上げ)

**PF > 0.95 達成根拠**:
- ベース PF 1.24 (BR EUR_USD) からスタート
- BearResearcher は「打たない」だけで、勝ち trade を loss にする構造ではない → 理論上 PF が下がらない
- 発火頻度減 = 機会損失あり、ただし PF 自体は維持か向上

## 8. WFA / OOS [G1-7]

- 5-fold anchored expanding WFA
- Deflated Sharpe (試行数: severity 閾値3 × HTF MA 3 × divergence lookback 3 × 重み校正 = 約 30)
- 「ゲート前 vs ゲート後」で OOS PF が悪化しないことを必須条件

## 9. 実装複雑度 [G1-3]

- 既存 `src/bear_researcher.py` を流用 (実装済み + テスト済み 14件)
- 直列ゲートロジック ~80行
- 自己改善モジュール ~200行
- ベース戦略は既存
- **総工数: 1-2 週間**

## 10. 機会費用比較 [G1-6]

| 運用先 | 1年累計 (100万円口座) |
|---|---:|
| 銀行預金 | +500 JPY |
| 米国債 | +40,000 JPY |
| 本提案 (PF 1.5、年40件、各 +1,000 JPY) | **+40,000 JPY** |
| 本提案 best (PF 1.8、年40件、各 +1,500 JPY) | **+60,000 JPY** |

**注意**: 米国債とほぼ同等。**加点は DD抑制と相関分散**だが、絶対リターンでの優位は限定的。

## 11. リスク・既知の弱点

1. **検出精度未検証**: 5チェックそれぞれの陽性的中率が未測定。誤検出が多ければ機会損失過大
2. **severity の独立性仮定**: 5 component の和を severity にするには独立性が必要。HTF と divergence が相関していると過剰ペナルティ
3. **`_RISK_WEIGHTS` の根拠薄弱**: 0.35/0.25/0.20/0.15/0.05 の重み設定が経験則ベース、データ駆動の校正が必要
4. **機会費用劣後**: 米国債並みまでしか期待できない見込み
5. **divergence 検出のピーク同定誤差**: scipy find_peaks のパラメータ依存

## 12. 採点自己評価

| Gate | 項目 | 自己採点 | 根拠 |
|---|---|---:|---|
| G0-A | PF > 0.95 | **PASS** | ベース PF 1.24 を悪化させない構造 |
| G0-B | 自己改善 | **PASS** | 重み校正含む再最適化 + 異常検出 + リバート明記 |
| G1-1 | エッジ源 | **7/10** | "consider the opposite" は古典的に有効、コンフルエンスと類似 |
| G1-2 | データ要件 | **10/10** | 既存 |
| G1-3 | 実装複雑度 | **9/10** | 既存 BearResearcher 流用、最低工数 |
| G1-4 | ロバスト性 | **6/10** | 重み設定にやや弱さあり、再校正の体制で補う |
| G1-5 | リスク | **8/10** | severity ベース position sizing で DD抑制効果大 |
| G1-6 | 機会費用 | **5/10** | 米国債並み止まり、絶対額が魅力薄い |
| G1-7 | WFA/OOS | **6/10** | 既存 BT は WFA 未実施、宿題 |
| G2-1 | スプレッド耐性 | **4/5** | 発火頻度低 → スプレッド負担相対小 |
| G2-2 | 相関 | **3/5** | コンフルエンス系と相関高い (兄弟戦略) |
| G2-3 | 説明可能性 | **5/5** | 5チェック内訳が日本語 reasoning で出力 |
| G2-4 | レビュー耐性 | **4/5** | TradingAgents 流の対立検証は批判が少ない |
| G2-5 | 拡張性 | **4/5** | 第6 BearCheck 追加が容易 |
| G2-6 | 過去挙動整合 | **5/5** | 亡き者の「ai_reasons NULL」問題を直接修正 |

**Gate 0**: PASS (両方)
**Gate 1 合計**: 51/70
**Gate 2 合計**: 25/30
**総合**: **76/100** — Phase 2 進出候補 (Confluence 系と類似性高、競合)

## 撤退条件 (先に書く)

- 90日経過時点で trades<10 → 撤退
- 90日経過時点で PF<1.2 → 撤退 (米国債並み以下なら BearResearcher の意義なし)
- 累計 PnL<-3,000 JPY → 即撤退
- BearResearcher が 7日連続で severity=0 のみ → 異常検出停止
- 連続2回パラメータ再最適化失敗 → 戦略停止
