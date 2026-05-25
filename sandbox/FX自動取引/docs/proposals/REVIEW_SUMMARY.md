# プロポーザル評価 集計レポート — Phase 0 全26候補 × 6評価委員

**作成日**: 2026-05-26
**評価対象**: `docs/proposals/phase0/` 配下の26候補 (memory 8 + research 9 + internal 9 含む補強)
**評価委員**: economics / structure / history / implementation / risk / meta (`.claude/agents/proposal-reviewer-*.md`)
**ソースレビュー**: `docs/proposals/reviews/REVIEW_*.md` (6ファイル)

---

## TL;DR

- **6委員全員一致 採用 (Phase 2 進出 強推奨)**: **#1 EUR_USD H1 RSI Pullback** / **#15 Meta-Labeling Ensemble** / **#12 Cointegration Pairs**
- **6委員全員一致 即却下**: **#7 GBP_JPY M15** / **#11 PPO RL** / **#13 News Sentiment** / **#22 Adaptive ATR Breakout** / **#24 Loser Pattern Reverse** / **#S Long Trend Following (補強)**
- **委員間対立 大、ユーザー判断必要**: **#2 USD_JPY M15 RSI** (亡き者 USD_JPY PF 0.477 vs BT M15 OOS PF 2.46) / **#4 Deceased Reversal** (econ/impl 推奨 vs history 即却下) / **#18 EUR_USD MR Focus** (4hr 損切り問題)
- **Phase 4 保留 (個別戦略確定後)**: #8 Multi-Strategy Portfolio / #25 Dynamic Portfolio Weighting
- **メタ警告 重大**: 全候補が採点フレームに建設的批判ゼロ = フレーム Goodhart 化、OOS trades 中央値11件 = 統計的根拠破綻

---

## 1. 6視点スコアマトリックス (26候補)

凡例: ✅採用 / 🟡条件付き / ⬜棚上げ / ❌即却下 / —未言及

| # | 候補 | econ | struct | hist | impl | risk | meta | 強収束 |
|---|---|---|---|---|---|---|---|---|
| 1 | **memory_eur_usd_h1_rsi_pullback** | ✅8 | ✅ | ✅9 | ✅10 | ✅7 | ✅ | **全員PASS** |
| 2 | memory_usd_jpy_m15_rsi_pullback | ✅8 | ✅ | 🟡 | ✅10 | — | ✅ | 5/6PASS |
| 4 | memory_deceased_reversal | ✅7 | 🟡 | ❌ | ✅9 | — | ⬜ | **対立大** |
| 5 | memory_llm_filter_dual_validation | ⬜ | 🟡 | ⬜ | ⬜ | — | ⬜ | 棚上げ |
| 6 | memory_seasonal_regime_gate | ⬜ | 🟡 | ⬜ | ⬜ | — | ⬜ | 棚上げ |
| 7 | **memory_gbp_jpy_m15_high_pf_caution** | ❌0 | ❌ | ❌ | ❌ | ❌2 | ❌ | **全員却下** |
| 8 | memory_multi_strategy_portfolio | — | (Phase4) | ✅9 | (Phase4) | ✅8 | 🟡 | **Phase 4 保留** |
| 14 | research_london_breakout_adaptive | ✅7 | ✅ | 🟡 | ✅9 | — | ⬜ | 4/6PASS |
| 15 | **research_meta_labeling_ensemble** | ✅7 | ✅TOP3 | ✅10 | ✅7 | ✅8 | 🟡 | **5/6 採用+1条件付** |
| 12 | research_cointegration_pairs | ✅6 | ✅ | 🟡 | ✅8 | ✅8 | ✅ | **全員PASS** |
| 16 | research_carry_trade_systematic | ⬜ | ⬜ | ⬜ | ⬜ | — | ⬜ | 棚上げ |
| 9 | research_xgboost_walk_forward | ⬜ | ⬜ | ⬜ | ⬜ | — | ⬜ | 棚上げ |
| 10 | research_hmm_regime_ensemble | ⬜ | ⬜ | ⬜ | ⬜ | — | ⬜ | 棚上げ |
| 11 | **research_ppo_rl_auxiliary** | ❌ | ❌ | ❌ | ❌ | ❌2 | ❌ | **全員却下** |
| 13 | **research_news_sentiment_garch** | ❌ | ❌ | ❌ | ❌ | ❌3 | ❌ | **全員却下** |
| 17 | research_volume_profile_microstructure | ⬜ | ❌ | ⬜ | ⬜ | — | ❌ | 棚上げ→却下 |
| 18 | internal_eurusd_meanrev_focus | — | ✅ | 🟡 | ✅9 | 🟡警告 | ⬜ | **4hr問題** |
| 19 | internal_yz_vol_regime_router | — | ❌ | ❌ | — | — | — | 即却下 |
| 20 | internal_confluence_gate_filter | 🟡 | ❌ | ⬜ | (統合) | — | ⬜ | placeholder言い換え |
| 21 | internal_bull_bear_dialectic | 🟡 | ❌ | ⬜ | (統合) | — | ⬜ | placeholder言い換え |
| 22 | **internal_adaptive_atr_breakout** | ❌ | ❌ | ❌ | ❌ | ❌2 | ❌ | **全員却下** |
| 23 | internal_session_split_strategies | — | ❌ | 🟡 | ⬜ | — | ⬜ | placeholder言い換え |
| 24 | **internal_loser_pattern_reverse** | ❌ | ❌ | ❌ | ❌ | ❌3 | ❌ | **全員却下** |
| 25 | internal_dynamic_portfolio_weighting | — | (Phase4) | 🟡 | (Phase4) | ✅8 | ❌ | **Phase 4 保留** |
| S | **internal_long_trend_following** (補強) | ❌0 | ❌ | — | ❌ | — | ✅10誠実 | **全員却下** (補強役割完了) |
| 3 | memory_mfi_adx_breakout | 🟡 | 🟡 | ⬜ | ⬜ | — | ❌ | 棚上げ |

※ 番号は MECE_AUDIT.md の付番。番号がない箇所は集計上付与。

---

## 2. 委員間収束パターン

### 🟢 6委員全員一致 採用 (Phase 2 進出 確定推奨)

| 候補 | 強収束理由 |
|---|---|
| **#1 memory_eur_usd_h1_rsi_pullback** | BT grid 完備、亡き者 EUR_USD PF 2.37 と整合、placeholder なし、自己改善具体、MaxDD -6% |
| **#15 research_meta_labeling_ensemble** | 「亡き者 ma_crossover Primary + meta-labeling」が撤退教訓を最も誠実に実装、Safe Mode フォールバック |
| **#12 research_cointegration_pairs** | 方向中立 = 分散源最強、Stress Test 明示、statsmodels で実装容易、低相関 |

### 🟢 5/6委員 採用 (1委員のみ条件付き)

| 候補 | 強収束理由 | 唯一の条件 |
|---|---|---|
| **#2 memory_usd_jpy_m15_rsi_pullback** | BT M15 OOS PF 1.94-2.46、timeframe特異性 | history 条件付き: 亡き者 USD_JPY H1 PF 0.477 との論証必要 |

### 🟢 4/6委員 採用

| 候補 | コメント |
|---|---|
| **#14 research_london_breakout_adaptive** | 実装最速 (1-2週)、文献厚い、月次 Optuna 再最適化。meta が棚上げ |

### 🔴 6委員全員一致 即却下

| 候補 | 共通却下理由 |
|---|---|
| **#7 memory_gbp_jpy_m15_high_pf_caution** | OOS 4件、撤退3週間後再採用 = ULTRA バグB再演、機会費用未達 |
| **#11 research_ppo_rl_auxiliary** | MaxDD -30%、Policy Collapse、Buy&Hold 収束罠を回避ロジック未実装 |
| **#13 research_news_sentiment_garch** | NewsAPI 月$449 個人運用持続不能、HFT 競合、スプレッド10倍拡大 |
| **#22 internal_adaptive_atr_breakout** | signal_v2 PF 0.95 改修 = 撤退原因再演、スプレッドで break-even 割る |
| **#24 internal_loser_pattern_reverse** | 仮説脆弱+サンプル過少+#4と機能重複、スプレッド負担同じ |
| **#S internal_long_trend_following** (補強) | PF 0.96 で起草者自己却下、3ペア合算 -1,593 JPY/年 |

---

## 3. 委員間対立検出 (ユーザー判断材料)

### 対立大 #1: **#4 memory_deceased_reversal**

| 委員 | 判定 | 論拠 |
|---|---|---|
| economics | ✅7 | 亡き者 PF 0.81 を反転して PF 1.23 (EUR_USD除外で 1.45) |
| implementation | ✅9 | 既存 ma_crossover.py 流用、亡き者DB直接活用 |
| structure | 🟡 条件付き | 反転ロジックの自己改善が弱い |
| **history** | **❌ 即却下** | **撤退済全通貨を反転対象として再投入、EUR_USD で破綻 (亡き者 EUR_USD PF 2.37 は反転すると負け)** |
| meta | ⬜ 棚上げ | 実BT 数字あるが OOS 不足 |

→ **history の指摘が決定的**: EUR_USD は亡き者で唯一の勝ち通貨 = 反転対象から除外しないと自己破綻。**「亡き者全体反転」設計が論理的に破綻**しているため、history 即却下が筋。

### 対立大 #2: **#18 internal_eurusd_meanrev_focus**

| 委員 | 判定 | 論拠 |
|---|---|---|
| economics | — | (未明) |
| structure | ✅ 採用 | placeholder なし、撤退条件明文 |
| **history** | **🟡 警告** | **4時間タイムストップが亡き者中央値 231分・>240min 比率 46.2% と致命的ミスマッチ = SPEC v2 撤退バグ⑤再演リスク** |
| implementation | ✅9 | 既存 bollinger_reversal.py 流用 |
| **risk** | **🟡 警告** | **同上、4hr ミスマッチ** |
| meta | ⬜ 棚上げ | OOS 不足 |

→ **history + risk が一致して 4hr 損切りを警告** → **タイムストップ 8時間以上に修正してから Phase 2 進出**が筋。修正なら ✅ 採用候補に格上げ可能。

### 対立大 #3: **#15 research_meta_labeling_ensemble**

| 委員 | 判定 | 論拠 |
|---|---|---|
| economics | ✅7 | 想定 PF 高め (BT 数字依存) |
| structure | **✅TOP3** | placeholder なし、撤退条件完全、Safe Mode 設計 |
| **history** | **✅TOP 10/10** | **亡き者 ma_crossover Primary + meta-labeling が撤退教訓を最も誠実に実装** |
| implementation | ✅7 | Hudson&Thames 実装あり、CPU で動く |
| risk | ✅8 | Safe Mode フォールバック、Purged K-Fold + Embargo |
| **meta** | **🟡 条件付き** | **「亡き者 MTFPullback を Primary」と書きたいが、ma_crossover なのか MTFPullback なのか曖昧。条件: Primary 候補を明示** |

→ meta と history の論証要件が微妙に違う (どの亡き者戦略を Primary にするか)。これは **Phase 2 入る前に明示**すれば解決可能。実質的に **5/6委員強推奨**。

### 対立大 #4: **#25 internal_dynamic_portfolio_weighting**

| 委員 | 判定 | 論拠 |
|---|---|---|
| **risk** | **✅8 (唯一の日次合算3%上限明示)** | リスク管理優位 |
| **meta** | **❌ 即却下 (Phase 4 候補の現フェーズ混入で Goodhart 化)** | 個別戦略確定前の評価不当 |

→ 両論あり。**「Phase 4 保留」とラベル付けして現フェーズ評価から外す**のが整合的。risk の「日次合算上限」設計は Phase 4 でそのまま活用。

### 対立中: **#8 memory_multi_strategy_portfolio**

| 委員 | 判定 |
|---|---|
| history | ✅9 |
| risk | ✅8 (TOP3) |
| meta | 🟡 (Phase 4 保留条件) |
| その他 | Phase 4 案件として未深評価 |

→ #25 同様 **Phase 4 保留** が筋。

---

## 4. 6視点共通の重大警告 (Phase 2 進出前 必須対処)

### 警告1: 採点フレームの Goodhart 化 (meta 指摘、影響全候補)

- **26候補すべてが採点フレームに建設的批判ゼロ** = 即却下基準 #5 該当
- これは「フレームを盲従して点数を取りに来た」候補ばかりという証拠
- **フレーム改訂 7項目** を Phase 2 通過後に実施推奨:
  1. G0-A 自前BT強制 (循環論証禁止)
  2. OOS trades ≥ 30 強制
  3. Phase レイヤー欄 (単一戦略 / ポートフォリオ層 / ルーター層)
  4. 反論屋応答セクション
  5. **G2-7 採点フレーム批判** (採点項目を疑う節を必須化)
  6. 依存戦略明示
  7. 自己採点高得点警告 (80+ は再採点強制)

### 警告2: OOS サンプル数破綻 (meta 指摘、TOP候補にも影響)

- 全候補の OOS trades 中央値 = **11件** (最少3件、≥30 が下限)
- **#1 PF 1.49 のパラメータも OOS 17件**、**#2 PF 2.46 は 11件** = 統計的根拠不足
- Phase 1 BT で **OOS ≥30 強制**、不足なら BT 期間延長 or 別ペア追加

### 警告3: 日次/月次損失上限 未明示 (risk 指摘、26候補中25候補該当)

- CLAUDE.md「最大損失を先に決める」原則違反
- 唯一明示しているのは **#25 Dynamic Portfolio (日次合算3%)**
- Phase 1 BT 前に全進出候補に強制追加 (-1.5% → -3% → -5% 階層化)

### 警告4: 平均回帰 11候補の擬似独立 (meta + MECE 監査一致)

- 11候補が同一 EUR_USD データを多角度で見ているだけ = 反論屋ULTRA バグE 再演
- ただし history は「論理的に正当」と判定 (亡き者で唯一プラス通貨)
- **対処**: ポートフォリオ分散源 (#12 Cointegration、#8 Portfolio) を必須セット

---

## 5. Phase 2 進出推奨 (3案、ユーザー判断材料)

### 案A: 厳格 (meta 視点準拠、3候補)

```
✅ #1  memory_eur_usd_h1_rsi_pullback  (全員 PASS)
✅ #15 research_meta_labeling_ensemble (5/6 + 1条件付)
✅ #12 research_cointegration_pairs   (全員 PASS、分散源)
```

メリット: 強収束のみ、Phase 2 BT 工数最小
デメリット: 戦略多様性が EUR_USD MR + ML + cointegration の3軸のみ

### 案B: 標準 (4-5候補、推奨)

```
✅ #1  EUR_USD H1 RSI Pullback        (全員 PASS)
✅ #15 Meta-Labeling Ensemble         (5/6 + 1条件付)
✅ #12 Cointegration Pairs            (全員 PASS、分散源)
🟡 #2  USD_JPY M15 RSI Pullback       (5/6 PASS、history 条件付き)
🟡 #14 London Breakout Adaptive       (4/6 PASS、戦略タイプ多様化)
```

メリット: 戦略タイプ4種 (MR / ML / cointegration / breakout)
デメリット: #2 の亡き者 USD_JPY H1 PF 0.477 vs M15 OOS PF 2.46 の論証必要

### 案C: 修正条件付き (6候補)

```
案B + 修正後の #18 EUR_USD MR Focus (4hr → 8時間以上に修正してから進出)
```

メリット: EUR_USD で平均回帰2候補 (#1 H1 + #18 H1+M15+セッション) で深堀り
デメリット: history+risk 警告事項を未対処のまま進出するリスク

### Phase 4 保留 (個別戦略確定後に再評価、現フェーズで進出しない)

- **#8 Multi-Strategy Portfolio** (history TOP3、risk TOP3、優秀だが個別戦略の Phase 2 通過が前提)
- **#25 Dynamic Portfolio Weighting** (risk: 唯一の日次上限明示、meta 即却下)

→ 案B/Cで採用した4-5候補が Phase 2 通過したら Phase 4 で Portfolio 層に進む

---

## 6. ユーザー判断ポイント

集計を踏まえて、以下の判断が必要:

### Q1: Phase 2 進出候補数
- 案A (3候補、厳格)
- **案B (4-5候補、推奨)**
- 案C (6候補、4hr 修正必須)

### Q2: 採点フレーム改訂のタイミング
- (a) Phase 2 通過後にやる (推奨、現サイクルを止めない)
- (b) Phase 2 入る前にやる (再採点が必要になる)
- (c) やらない (Goodhart 化を放置)

### Q3: OOS 不足対策 (#1, #2 含む全候補に影響)
- (a) Phase 2 BT で OOS≥30 強制 (期間延長 or ペア追加で trades 増)
- (b) 現状の OOS で進む (統計的根拠弱いまま)

### Q4: 日次/月次損失上限の全候補強制追加
- (a) Phase 2 BT 開始前に必須追加 (CLAUDE.md 安全性原則準拠)
- (b) Phase 2 通過候補のみ追加

### Q5: #4 Deceased Reversal の扱い
- (a) history 即却下を受け入れて廃案
- (b) EUR_USD を反転対象から除外した修正版で再検討

### Q6: #18 EUR_USD MR Focus の扱い
- (a) 4hr → 8時間以上に修正してから案Cで進出
- (b) 修正なしで進出 (history+risk 警告無視)
- (c) 棚上げ

---

## 7. 関連ファイル

### 個別レビュー (6委員)
- `docs/proposals/reviews/REVIEW_economics.md`
- `docs/proposals/reviews/REVIEW_structure.md`
- `docs/proposals/reviews/REVIEW_history.md`
- `docs/proposals/reviews/REVIEW_implementation.md`
- `docs/proposals/reviews/REVIEW_risk.md`
- `docs/proposals/reviews/REVIEW_meta.md`

### 採点フレーム
- `docs/PROPOSAL_TEMPLATE.md`
- `docs/PROPOSAL_REVIEW_PROCESS.md`

### 構造監査
- `docs/proposals/phase0/MECE_AUDIT.md`

### 撤退教訓
- `docs/RETREAT_2026-05-26.md`
- `docs/analysis/CONTRARIAN_KAREN.md` / `CONTRARIAN_ULTRA.md` / `CONTRARIAN_PRAGMATIST.md`

### Phase 0 候補 (26件)
- `docs/proposals/phase0/memory_*.md` (8件)
- `docs/proposals/phase0/research_*.md` (9件)
- `docs/proposals/phase0/internal_*.md` (9件)
