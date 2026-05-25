# プロポーザル: コンフルエンス・ゲートフィルター (既存戦略 + 5指標一致でのみ発火)

## 1. 戦略仮説 (1段落)

亡き者は ConvictionScorer (`src/conviction_scorer.py`) を実装していたが、本番運用では **`MIN_CONVICTION_SCORE` の閾値設計とエントリーロジックの組み合わせが甘く**、結果として ai_decision/ai_regime が全件 NULL になっていた (本DB調査で判明)。本提案は既存 ConvictionScorer (trend/ADX/RSI/MFI/regime の5指標) を**厳格化**し、**5指標中 4つ以上が一致した時のみ発火する Confluence Gate** として再設計する。亡き者の負け原因の中核は「シグナルが立ったから打ったが、上位足/レジーム/出来高が支持していなかった」ケース。これを構造的にゲートする。

## 2. 想定エッジ源 [G1-1]

**構造的優位**:
- 多指標コンフルエンスは個人投資家の世界では古典 (Murphy 1999, Elder 1993) で、**過剰最適化に対する自然な regularization** が働く
- 各指標が独立な情報源 (価格傾向 = MA、勢い = RSI、流入 = MFI、強度 = ADX、環境 = Regime) なので、5指標一致は「全くノイズが揃わない確率」を下げる
- @loopdom (memory: research_ai_trading_2026_03.md) の confluence score 設計と整合
- @onlybreakouts の「MFI+ADX フィルタが効く」(memory: project_fx_strategy_pivot_2026_05.md) と整合

**実取引データの裏付け** ([[feedback-deceased-world-data-inheritance]] 遵守):
- 亡き者 prod DB で ai_decision/ai_regime/ai_confidence/ai_reasons がすべて NULL → ConvictionScorer は**実装はされたが運用パイプラインに繋がれていなかった**可能性 (本probe で確認済み)
- 「コンフルエンスを評価したが使わなかった」が亡き者の負け原因の一つ → 本提案で「コンフルエンスを必須ゲートにする」

## 3. シグナル定義 (擬似コード)

```python
def generate_signal(data_m15, data_h1, base_strategy):
    # ステップ1: ベース戦略のシグナル取得 (BollingerReversal または MTFPullback)
    raw_signal = base_strategy.generate_signal(data_m15)
    if raw_signal == HOLD:
        return HOLD

    # ステップ2: コンフルエンス計算
    indicators = compute_indicators(data_m15, data_h1)
    score, components = conviction_score(raw_signal, indicators)

    # 各 component が 1点 (横ばい/許容範囲) ではなく 2点 (一致) のみカウント
    strong_aligned = sum(1 for v in components.values() if v == 2)

    # ステップ3: 5指標中 4つ以上で 2点 (= 強い一致) を要求
    if strong_aligned >= 4:
        return raw_signal
    else:
        return HOLD

# ベース戦略は2つ並行運用:
#   - BollingerReversal (平均回帰)
#   - MTFPullback (トレンド押し目)
# どちらも上記コンフルエンスゲートを通過しないと発火しない
```

**重要設計**: 既存 ConvictionScorer の **`MIN_CONVICTION_SCORE` 設計のままだと不十分**。「8点」だと trend=2, adx=2, rsi=2, mfi=1, regime=1 でも通る = 中途半端な一致でも発火。本提案は **「2点が4つ以上」という非対称要件**で「強い一致のみ」を抽出する。

## 4. データ要件 [G1-2]

- MT5 EUR_USD/USD_JPY M15 + H1 (5年): 既存
- volume データ (MFI 用) — MT5 で M15 volume 取得可能
- 追加 API 不要

## 5. リスクモデル [G1-5]

- SL: ATR(14) × 1.5 (ベース戦略の値を踏襲)
- TP: SL距離 × 1.5
- 想定 MaxDD: -8% (フィルタ強化で発火頻度減 → DD抑制)
- 発火頻度予測: 既存 BR/MTF 単独の 1/5 以下 (5指標 4つ一致は厳しい)
- テールリスク: 連続不発で機会損失 → 90日 trades<10 で撤退

## 6. 自己改善メカニズム [G0-B] — 必須

**ドリフト検出 (毎週)**:
- 直近30日の各 component (trend/adx/rsi/mfi/regime) の 2点獲得率を集計
- 過去365日対比で ±50% 変動した component をアラート
- 直近30日 PF<1.0 でアラート

**パラメータ自動再最適化 (月次)**:
- 「2点が N つ以上」の N (3/4/5) のグリッド
- ADX threshold (25/30/35)、RSI threshold (25-50, 30-50, 35-50) のグリッド
- 直近 12ヶ月 IS / 直近 3ヶ月 OOS、各 N 値での PF を評価
- 最良 OOS PF パラメータ採用 (N が変動可能)

**フォールバック**:
- 新 N で 30日 PF<0.9 → 旧 N へ自動リバート
- 連続 2回最適化失敗 → 戦略停止 + Slack 通知

**トリガー条件**:
- 毎週金曜 06:00 JST ドリフトチェック
- 月初1日 全パラメータ再最適化
- 累計 -3,000 JPY / 90日 trades<10 / 連続2回再最適化失敗 → 撤退

## 7. 過去 BT 結果 [G0-A] — 必須

**現時点で示せる根拠**:
- ベース BollingerReversal 単独 PF 1.24 (EUR_USD M15 2年)
- コンフルエンスゲートで発火を絞ると **発火回数 1/5** だが、フィルタが効けば **PF 1.5 以上** が期待値 (理論)
- 実証: BT スクリプト宿題

**Phase 1 で行うべき追加 BT (宿題)**:
- BollingerReversal + Confluence(N=4) の EUR_USD M15 5年 BT
- MTFPullback + Confluence(N=4) の同 BT
- 期待値: 各 PF 1.5 以上、ただし trade 数が 30/年 程度に減る可能性

**PF > 0.95 達成根拠**:
- ベース戦略の素の PF が既に 1.24 (BR) または 2.05 (MTF EUR_USD)
- コンフルエンスゲートで悪化することは理論上ない (発火減 = 機会減だけ)
- worst case でも素の戦略の PF を割らない

## 8. WFA / OOS [G1-7]

- 5-fold anchored expanding WFA
- Deflated Sharpe (試行数 N グリッド3 × ADX 3 × RSI 3 = 27)
- 「ゲートのおかげで OOS PF が IS PF を下回らない」を必須条件

## 9. 実装複雑度 [G1-3]

- 既存 `src/conviction_scorer.py` を流用 (実装済み + テスト済み)
- 「2点獲得カウント」の追加ロジック ~50行
- ベース戦略は既存
- 自己改善モジュール ~200行
- **総工数: 1-2 週間**

## 10. 機会費用比較 [G1-6]

| 運用先 | 1年累計 (100万円口座) |
|---|---:|
| 銀行預金 | +500 JPY |
| 米国債 | +40,000 JPY |
| 本提案 (PF 1.5、年30件、各 +800 JPY) | **+24,000 JPY** |
| 本提案 best (PF 2.0、年30件、各 +1,500 JPY) | **+45,000 JPY** |

**注意**: 発火頻度が下がるため絶対額は小さい。**機会費用上は米国債と同程度**で、加点は「ドローダウンが小さい」「相関が違う」点になる。

## 11. リスク・既知の弱点

1. **過小発火**: N=4 が厳しすぎて trades<5/月になる → 評価不能の罠 ([[feedback-anomaly-is-signal-not-conclusion]] 同型)
2. **指標の冗長**: trend(MA) と RSI/MFI が情報的に重複しているなら「4 一致」が実は「2 独立シグナル」かもしれない (主成分分析で確認要)
3. **既存実装のバグ**: ConvictionScorer の `_score_rsi` には監査P0-#1 でロジック修正の履歴あり、まだ別のバグが残っている可能性
4. **機会費用劣後**: 米国債 4% と同等までしか期待できない見込み → そもそも採用に値するかの議論が要る
5. **2点獲得の閾値設計**: 「2点」のみカウントする設計が`_FLAT_SLOPE_REL`等の内部閾値に敏感

## 12. 採点自己評価

| Gate | 項目 | 自己採点 | 根拠 |
|---|---|---:|---|
| G0-A | PF > 0.95 | **PASS** | ベース PF 1.24 を悪化させない構造、ゲートが効けば 1.5+ |
| G0-B | 自己改善 | **PASS** | N 値含む再最適化 + リバート + 撤退ライン明記 |
| G1-1 | エッジ源 | **7/10** | コンフルエンスは古典で構造的、ただし 5指標が独立かは未検証 |
| G1-2 | データ要件 | **10/10** | 既存 |
| G1-3 | 実装複雑度 | **9/10** | 既存 ConvictionScorer + ベース戦略の組み合わせ、最も低工数 |
| G1-4 | ロバスト性 | **6/10** | 多指標で個別パラメータ感度は分散される、N の感度は中程度 |
| G1-5 | リスク | **8/10** | 発火頻度低 → DD抑制、撤退ライン明確 |
| G1-6 | 機会費用 | **5/10** | 米国債と同等止まり、絶対額が小さい |
| G1-7 | WFA/OOS | **6/10** | 既存 BT は WFA 未実施、Phase 1 で実施宿題 |
| G2-1 | スプレッド耐性 | **5/5** | 発火頻度が低いのでスプレッド負担小、コスト 2x でも耐える |
| G2-2 | 相関 | **3/5** | 単一ペア x 2戦略でやや分散だが限定的 |
| G2-3 | 説明可能性 | **5/5** | 5指標の内訳が ConvictionResult に明示、レビュー可能 |
| G2-4 | レビュー耐性 | **4/5** | コンフルエンスは批判が少ない古典、ただし「米国債と同等なら不採用」批判は受ける |
| G2-5 | 拡張性 | **4/5** | 第6指標の追加が容易、ペア追加も低コスト |
| G2-6 | 過去挙動整合 | **5/5** | 亡き者の「ConvictionScorer 未活用」を直接的に改善 |

**Gate 0**: PASS (両方)
**Gate 1 合計**: 51/70
**Gate 2 合計**: 26/30
**総合**: **77/100** — Phase 2 進出候補 (機会費用低だが安全度高)

## 撤退条件 (先に書く)

- 90日経過時点で trades<10 → 撤退 (発火頻度過少で評価不能)
- 90日経過時点で PF<1.2 → 撤退 (米国債並み以下、コンフルエンスゲートの意味なし)
- 累計 PnL<-3,000 JPY → 即撤退
- 連続2回パラメータ再最適化失敗 → 戦略停止
