# Phase 0 候補手法ロングリスト — Researcher エージェント調査結果

**調査日**: 2026-05-26
**スコープ**: SPEC v2 撤退 (2026-05-26) を受けた、PF > 0.95 を実証可能な FX 自動取引手法のWeb調査
**対象**: 日本人個人投資家 / 100-500万円スケール / MT5 + Python 実装可能性
**採点フレーム**: `docs/PROPOSAL_TEMPLATE.md`

---

## 候補一覧 (採点降順)

| # | プロポーザル名 | ファイル | G0-A | G0-B | G1 /70 | G2 /30 | **総合 /100** | Phase 1 進出 |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **Meta-Labeling + 既存シグナルアンサンブル** | `research_meta_labeling_ensemble.md` | ○ | ○ | 58 | 27 | **85** | ★ TOP 1 推奨 |
| 2 | **コインテグレーション + Bollinger Z-Score** | `research_cointegration_pairs.md` | ○ | ○ | 56 | 26 | **82** | ★ TOP 2 推奨 |
| 3 | **London Breakout + 適応的フィルタ** | `research_london_breakout_adaptive.md` | ○ | ○ | 58 | 24 | **82** | ★ TOP 3 推奨 |
| 4 | **HMM レジーム検出 + 専用 ML アンサンブル** | `research_hmm_regime_ensemble.md` | ○ | ○ | 54 | 23 | **77** | 進出推奨 |
| 5 | **XGBoost + Walk-Forward Optimization** | `research_xgboost_walk_forward.md` | △ | ○ | 54 | 22 | **76** | 進出推奨 (要 BT) |
| 6 | **体系的キャリートレード + リスクオフフィルタ** | `research_carry_trade_systematic.md` | ○ | ○ | 49 | 26 | **75** | 進出推奨 (テールリスク注意) |
| 7 | Volume Profile + Value Area 反転 | `research_volume_profile_microstructure.md` | △ | ○ | 46 | 21 | 67 | 保留 (FX 適用に疑問) |
| 8 | PPO Reinforcement Learning + Auxiliary Task | `research_ppo_rl_auxiliary.md` | △ | ○ | 39 | 16 | 55 | 棚上げ (実用性低) |
| 9 | 経済ニュースセンチメント (BERT) + GARCH | `research_news_sentiment_garch.md` | △ | ○ | 38 | 18 | 56 | 棚上げ (データコスト・スプレッド脆弱) |

---

## サマリ

### Gate 0 PASS 候補: 9件中 6件 (○) + 3件 (△ 条件付き)
- **○ (PASS)**: meta-labeling, cointegration, london_breakout, hmm_regime, carry_trade — **既存研究で PF/Sharpe の改善実証あり**
- **△ (条件付き)**: xgboost_wfa, volume_profile, ppo_rl, news_sentiment — 自前 BT で PF > 0.95 検証必要

### Gate 1 + Gate 2 合計 70点以上 (Phase 1 進出基準): **6件**
1. meta-labeling (85)
2. cointegration (82)
3. london_breakout (82)
4. hmm_regime (77)
5. xgboost_wfa (76)
6. carry_trade (75)

---

## TOP 3 推奨 (Phase 1 BT 優先実施)

### 1位: Meta-Labeling + アンサンブル (85/100)
**推奨理由**:
- **Lopez de Prado の学術的裏付け** (Cornell, Guggenheim) と Hudson & Thames 等の実証 (**Sharpe 1.4 → 2.0**)
- **亡き者の MTFPullback を Primary として meta-labeling 適用するのが最適なテストケース** — 過去挙動データの直接的反証材料活用 (G2-6 構造的整合)
- 完全に説明可能 (Primary は SMA cross、Secondary は feature_importance で可視化)
- 反論屋 (karen/ultrathink/pragmatist) 耐性が極めて高い
- **データ要件最小** (既存 MT5 + 既存特徴量)

### 2位: コインテグレーション ペアトレード (82/100)
**推奨理由**:
- **方向中立 (market-neutral) で他戦略と圧倒的低相関** — ポートフォリオ分散源として最強
- Engle-Granger 以来 30年以上の学術的実証
- **既存研究で PF 1.3-2.0 報告多数** (Lemishko 2024, Applied Economics 2018)
- 実装最速 (**2週間**), `statsmodels.coint` のみで実装可能
- 動的ペア再選定 + ブラックリスト機構で関係崩壊耐性

### 3位: London Breakout + 適応的フィルタ (82/100)
**推奨理由**:
- **実装最速 (1-2週間)** — 今回候補の中で最短
- **取引頻度高 → 5年で 1000-2000 トレード** → 統計的有意性高
- GitHub に既存実装多数 (MHZardary, adrian-baehler 等)
- セッション構造的優位 + 時間構造的非効率 = 長期ロバスト
- 完全に説明可能 (アジアレンジ → ロンドン突破 → 順張り)

---

## 棚上げ・却下候補 (Phase 1 進出非推奨)

### PPO RL + Auxiliary Task (55/100)
- 学習コスト過大 (8-12時間/回 + ハイパラ探索で 100時間+)
- **コミッション込みで Buy & Hold に収束する罠** (arXiv 2411.01456 明示警告)
- シード依存・ブラックボックス・MaxDD 大
- 個人投資家 100-500万円スケールに **オーバーキル**

### 経済ニュースセンチメント (56/100)
- **NewsAPI 有料 ($449/月) または GDELT 15分遅延** = データボトルネック
- **スプレッド拡大が致命的** (FOMC 時 2pip → 10-20pip)
- HFT 競合に勝てる構造ではない
- 「分散源」として将来再評価候補

### Volume Profile (67/100)
- FX の OTC 構造で **Tick Volume ≠ 真の出来高**
- Trending 期で機能しない
- Mainstream 戦略のリスク (stop hunt 標的)
- 上位6候補で十分な多様性確保 → 保留

---

## 推奨アクション

### Phase 1 (簡易 BT スクリーニング)
**並列で 3 戦略を BT 実装・比較**:
1. **Meta-Labeling** を最優先で実装 (亡き者 MTFPullback を Primary として再活用)
2. **Cointegration** を並列で実装 (`statsmodels.coint` のみ、2週間)
3. **London Breakout** を並列で実装 (1-2週間、GitHub 雛形流用)

### Phase 2 (精査 BT)
- Phase 1 で PF > 1.3 を達成した戦略を WFA/OOS/Deflated Sharpe で精査
- 反論屋 3エージェント (karen / ultrathink / pragmatist) で別データの別観点レビュー

### Phase 3 (採用判断 + SPEC v3 起草)
- 採用された手法に合わせて SPEC v3 を新規起草
- 撤退条件を **事前** に書く (PROPOSAL_TEMPLATE 不採用基準 3 準拠)

### 補完戦略候補 (将来再評価)
- **HMM レジーム検出**: メインストラテジー確立後、上位 wrapper として再評価
- **XGBoost WFO**: meta-labeling と統合する形 (Primary を XGBoost にする) で再評価
- **Carry Trade**: 中長期分散源として、メイン戦略確立後の補完候補

---

## 調査の留意点

### 採用判断時に確認すべきこと
1. **「過去で効いた」だけの戦略は除外** — Lopez de Prado, Engle-Granger 等の **理論的根拠** を持つ手法を優先した
2. **「Holy Grail」系業者の宣伝を全て除外** — 学術論文 + GitHub 実装の組み合わせで構成
3. **2024-2026 の最新研究を優先** — 古典手法でも2024年以降の再評価を確認
4. **日本の金商法を考慮** — ニュースセンチメント戦略 (経済情報の機械的活用) はグレーゾーン、法務確認推奨

### 経済性 Gate の事前検証
PROPOSAL_TEMPLATE Section 不採用基準 (3) **撤退条件が事前に書かれていない** に該当しないよう、各プロポーザルの Section 6 (自己改善メカニズム) に **「撤退条件 / 取引停止条件」を明示**。

---

## 出力ディレクトリ
- `docs/proposals/phase0/research_meta_labeling_ensemble.md`
- `docs/proposals/phase0/research_cointegration_pairs.md`
- `docs/proposals/phase0/research_london_breakout_adaptive.md`
- `docs/proposals/phase0/research_hmm_regime_ensemble.md`
- `docs/proposals/phase0/research_xgboost_walk_forward.md`
- `docs/proposals/phase0/research_carry_trade_systematic.md`
- `docs/proposals/phase0/research_volume_profile_microstructure.md`
- `docs/proposals/phase0/research_ppo_rl_auxiliary.md`
- `docs/proposals/phase0/research_news_sentiment_garch.md`

---

## 主要参考文献

### 学術論文
- Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley
- Bailey, D.H. & Lopez de Prado, M. (2014). *The Deflated Sharpe Ratio*
- Hamilton, J.D. (1989). *A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle* — HMM レジーム switching の起源
- Engle & Granger (1987). *Cointegration and Error Correction* — コインテグレーション理論の原典
- Bodilsen (2025). *Exploiting News Analytics for Volatility Forecasting* (Wiley)
- arXiv 2411.01456 (2024). *Improving Deep Reinforcement Learning Agent Trading Performance in Forex using Auxiliary Task*

### 実装リソース
- [Quantinsti Walk-Forward XGBoost](https://blog.quantinsti.com/walk-forward-optimization-python-xgboost-stock-prediction/)
- [Quantinsti HMM Regime Adaptive](https://blog.quantinsti.com/regime-adaptive-trading-python/)
- [Hudson & Thames Meta-Labeling](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)
- [Macrosynergy FX Carry](https://macrosynergy.com/research/how-to-use-fx-carry-in-trading-strategies/)
- [GitHub MHZardary London Breakout](https://github.com/MHZardary/london-strategy-backtest)
- [mlfinpy Python Library](https://mlfinpy.readthedocs.io/)
- [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3)
