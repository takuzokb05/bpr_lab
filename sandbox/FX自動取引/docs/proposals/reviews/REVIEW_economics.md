# Phase 0 候補 経済性査読レポート

**査読委員**: proposal-reviewer-economics (code-quality-pragmatist 派生)
**査読日**: 2026-05-26
**対象**: `docs/proposals/phase0/` 配下の全 26 候補 (memory 8 / research 9 / internal 9)
**評価軸**: PF / Sharpe / MaxDD / 機会費用 (預金 0.05% / 米国債 4% / 全世界株 8%) 一本
**役割定義**: `.claude/agents/proposal-reviewer-economics.md`

---

## 0. 査読サマリ — 先に結論

### 0-1. スコア分布

| スコア帯 | 件数 | 該当候補 |
|---|---|---|
| 9-10 | 0 | — |
| 8 | 2 | A (memory_eur_usd_h1_rsi_pullback), B (memory_usd_jpy_m15_rsi_pullback) |
| 7 | 3 | D (memory_deceased_reversal 部分採用), L (research_london_breakout_adaptive), M (research_meta_labeling_ensemble) |
| 6 | 4 | C (memory_mfi_adx_breakout), E (memory_seasonal_regime_gate), J (research_cointegration_pairs), Q (internal_confluence_gate_filter) |
| 5 | 6 | H (research_hmm_regime_ensemble), N (research_carry_trade_systematic), P (internal_eurusd_meanrev_focus), T (internal_yz_vol_regime_router), U (internal_session_split_strategies), V (memory_llm_filter_dual_validation) |
| 3-4 | 5 | G (research_xgboost_walk_forward), O (research_volume_profile_microstructure), Q2 (internal_bull_bear_dialectic), W (memory_multi_strategy_portfolio: 個別未確定で減点), X (internal_dynamic_portfolio_weighting: 個別未確定で減点) |
| 1-2 | 4 | I (research_ppo_rl_auxiliary), K (research_news_sentiment_garch), R (internal_adaptive_atr_breakout), Y (internal_loser_pattern_reverse) |
| **0** | 2 | **F (memory_gbp_jpy_m15_high_pf_caution)**, **S (internal_long_trend_following)** |

### 0-2. 即却下件数: **8 件** (詳細は §2)

即却下基準:
1. PF<0.95 直接実証 / 自己 BT 実証
2. スプレッド込み PF<1.0
3. 「BT 未実施、動かしてみないと分からない」
4. 機会費用論証の欠落 / 機会費用が銀行預金以下
5. lot 換算で年間期待 PnL が銀行預金以下 (100万円口座で +5,000 JPY 未満)

### 0-3. TOP 5 推奨

経済性視点で **Phase 1 BT 進出を強く推奨**する候補:

| 順位 | 候補 | スコア | 主要 PF / 期待 PnL |
|---|---|---|---|
| 1 | **A. memory_eur_usd_h1_rsi_pullback** | 8/10 | 既存 BT グリッド OOS PF 1.34-1.49 実証、亡き者 +3,315 JPY 整合、+6〜12%/年想定 |
| 2 | **B. memory_usd_jpy_m15_rsi_pullback** | 8/10 | M15 BT グリッド OOS PF 1.94-2.46 (但 trades 11-15)、+8〜18%/年想定 |
| 3 | **L. research_london_breakout_adaptive** | 7/10 | 文献 PF 1.2-1.5、実装 1-2 週間、年取引数 1000+ で統計信頼性高、説明可能性最高 |
| 4 | **M. research_meta_labeling_ensemble** | 7/10 | Hudson&Thames Sharpe 1.4→2.0、亡き者 MTFPullback の Primary 流用で反証材料直接活用 |
| 5 | **D. memory_deceased_reversal (EUR_USD 除外版)** | 7/10 | 亡き者 DB から直接 PF 1.45 計算 (実数字)、+13〜20%/年想定。ただし OOS 11日間限定で要 Phase 2 WFA |

### 0-4. 経済性総括 (一行)

**24/26 候補が "未 BT" または "BT 結果未検証"。経済性視点で実証ベースの "数字" を持っているのは A/B/D/F の 4 候補のみ。それ以外は「期待」「仮説」「想定」止まりで、PROPOSAL_TEMPLATE.md G0-A の「PF > 0.95 を上回る成果を出せるか」を実証している候補は実質 3 件 (A, B, D)。**

---

## 1. 全候補スコア表

凡例: 採判 = 採用候補 ◯ / 条件付 △ / 却下 ✗

| # | 候補 | 戦略タイプ | 提示 PF (出典) | スプレ込 PF | 想定年 PnL (100万) | 機会費用比較 | 採判 | スコア |
|---|---|---|---|---|---|---|---|---|
| A | memory_eur_usd_h1_rsi_pullback | MR | **OOS 1.34-1.49** (実 BT グリッド) | 込み | +60,000〜+120,000 | 米国債超え/株式肉薄 | ◯ | **8** |
| B | memory_usd_jpy_m15_rsi_pullback | MR | **OOS 1.94-2.46** (実 BT グリッド、trades 11-15) | 込み | +80,000〜+180,000 | 株式並み | ◯ | **8** |
| C | memory_mfi_adx_breakout | BO | **未実施** (理論 1.3-1.7) | 未測定 | +100,000〜+250,000 (想定) | 株式超え (想定) | △ | 6 |
| D | memory_deceased_reversal (EUR_USD 除外版) | MR (反転) | **1.45** (亡き者 DB 64件、10日) | 込み (実取引) | +135,000 (想定) | 株式超え | △ | **7** |
| E | memory_seasonal_regime_gate | MR + REG フィルタ | ベース 1.4 + シナリオ依存 | 込み | +30,000〜+220,000 (シナリオ次第) | シナリオ次第 | △ | 6 |
| F | **memory_gbp_jpy_m15_high_pf_caution** | MR | OOS **7.38** (但 trades 4 件、統計無意味) | 込み | **+800 JPY/年 (起草者自認)** | **銀行預金以下** | **✗** | **0** |
| G | research_xgboost_walk_forward | ML | **未実施** (Quantinsti EUR/USD 赤字事例) | 未測定 | +150,000〜+250,000 (想定) | 株式超え (想定) | △ | 4 |
| H | research_hmm_regime_ensemble | ML+REG | **未実施 (FX)** Quantinsti BTC Sharpe 1.76 | 未測定 | +100,000〜+180,000 (想定) | 株式並み (想定) | △ | 5 |
| I | research_ppo_rl_auxiliary | ML(RL) | **未実施** 論文 Sharpe 0.47、Buy&Hold 収束警告 | 未測定 | +150,000〜+400,000 (高分散) | 高分散、株式超え 期待 | ✗ | **2** |
| J | research_cointegration_pairs | STAT | **未実施 (自前)** 文献 PF 1.3-2.0 | 未測定 | +80,000〜+150,000 (想定) | 株式並み | △ | 6 |
| K | research_news_sentiment_garch | EVENT | **未実施** 方向予測の実証なし | スプレッド拡大致命 | +80,000〜+200,000 (高分散) | 株式並み (想定) | ✗ | **2** |
| L | research_london_breakout_adaptive | BO | **未実施 (自前)** 文献 PF 1.2-1.5、フィルタ有 | 取引コスト軽 | +100,000〜+250,000 (想定) | 株式超え (想定) | ◯ | **7** |
| M | research_meta_labeling_ensemble | ML(フィルタ) | **未実施 (FX)** 文献 Sharpe 0.5→1.2, 1.4→2.0 | 込み (フィルタで削減) | +120,000〜+200,000 (想定) | 株式並み | ◯ | **7** |
| N | research_carry_trade_systematic | CARRY | **未実施 (自前)** 文献 Sharpe 0.3-0.5 / 1.29 | 取引極小 | +60,000〜+120,000 (想定) | 米国債と同等-株式並み | △ | 5 |
| O | research_volume_profile_microstructure | MR (VOLM) | **未実施** Tick Volume 妥当性疑念 | 未測定 | +80,000〜+180,000 (想定) | 株式並み (想定) | △ | 4 |
| P | internal_eurusd_meanrev_focus | MR | 1.24 (BollingerReversal、改善前) | 込み (1.5pip) | +180,000 (想定) / worst ±0 | 株式並み 期待 | △ | 5 |
| Q | internal_confluence_gate_filter | MR/TR + ゲート | **未実施** (理論 1.5+) | 込み (発火頻度低) | +24,000〜+45,000 (想定) | **米国債と同等以下** | △ | 6 |
| Q2 | internal_bull_bear_dialectic | MR + Bearゲート | **未実施** (理論 1.5+) | 込み | +40,000〜+60,000 (想定) | 米国債並み | △ | 4 |
| R | **internal_adaptive_atr_breakout** | BO | **0.95 (signal_v2、実証)** + 改修期待 1.2 | 込みで死亡 | worst -19,290 JPY (毀損) | **負け側、信号 v2 と同等で却下圏** | **✗** | **2** |
| **S** | **internal_long_trend_following** | TR | **3ペア合算 PF 0.96 (起草者自身が自己 BT で実証)** | 込み | **-1,593 JPY (実 BT)** | **銀行預金以下、起草者自身が却下推奨** | **✗** | **0** |
| T | internal_yz_vol_regime_router | MR + BO ルーター | LOW_VOL 1.24, HIGH_VOL **未実施** | 込み 部分 | +150,000 (LOW のみ) | 株式並み | △ | 5 |
| U | internal_session_split_strategies | MR + BO + EVENT回避 | **未実施 (セッション別)** BR 単独 1.24 | 込み | +60,000〜+90,000 (想定) | 米国債超え 期待 | △ | 5 |
| V | memory_llm_filter_dual_validation | MR + LLM フィルタ | ベース 1.4 + LLM 想定 1.7-1.9 | LLM 過去 BT 不可 | +80,000〜+170,000 (想定) | 株式並み | △ | 5 |
| W | memory_multi_strategy_portfolio | PF | 個別 1.34-2.46 → 想定 1.5-1.8 | 込み | +80,000〜+150,000 (想定) | 株式並み | △ | 4 (前提条件依存) |
| X | internal_dynamic_portfolio_weighting | PF | 個別 1.24-2.05 → 想定 1.4-1.8 | 込み | +120,000〜+180,000 (想定) | 株式超え 期待 | △ | 4 (前提条件依存) |
| Y | **internal_loser_pattern_reverse** | MR (反転) | **GBP_JPY 反転で実効 0.82 (起草者自認、スプレッド込み)** | **死亡** | +30,000 (USD_JPY 単独 で機能した場合) | **GBP_JPY は銀行以下、USD_JPY 7件で統計無意味** | **✗** | **2** |

### 補足: スコアの主な減点理由

- **スコア 0**: PF<0.95 が実 BT で実証されている / 機会費用が銀行預金以下
- **スコア 2**: 自己 BT 実証なし + 既知の構造欠陥 (スプレッド致命 / コミッション収束 / 信号 v2 再演)
- **スコア 4-5**: 自己 BT 未実施 / 機会費用論証が曖昧 / 「想定」止まり
- **スコア 6-7**: 文献または既存 BT で PF>1.0 のエビデンスあり、但し自前 FX BT は未実施
- **スコア 8**: 自己 BT グリッドで実証 PF 1.3+、機会費用論証あり

---

## 2. 即却下リスト (8 件)

### 2-1. ✗ S. internal_long_trend_following (スコア 0)

**即却下理由 (該当基準: 1, 5)**:
- **起草者自身が実 BT で PF 0.96 (3ペア合算) を実証**し、「Gate 0 G0-A FAIL」「銀行預金以下」と自認
- 5年累計 -1,593 JPY (実 BT)、起草者自身が「案 B 却下、MECE 補強の役割は果たした」と推奨
- USD_JPY 単独運用 (PF 1.74) という cherry-pick 救済案も「他の高 PF 候補 (A, B) に劣後」と自認
- **本査読の経済性視点でも完全に同意**。3ペア合算で signal_v2 と同水準の PF 0.95-0.96 を提示しておきながら採用提案するのは撤退教訓 RETREAT_2026-05-26 § バグ③「経済性 Gate 不在」と同じ罠

### 2-2. ✗ F. memory_gbp_jpy_m15_high_pf_caution (スコア 0)

**即却下理由 (該当基準: 5)**:
- OOS PF 7.38 は出ているが、**OOS trades = 4 件** で統計的に無意味 (Deflated Sharpe で確実に下限 1.0 割れ)
- 起草者自身が「年 4 件 × 1取引 +200 JPY/lot 1.0 = **年 +800 JPY @ 100万 = +0.08%**」と試算 → **銀行預金 (+500 JPY) と同水準**
- 起草者自身が「Phase 2 進出 NG (G1<50)」「却下推奨」と自認
- 反論屋 ULTRA バグ B (撤退済 GBP_JPY 再採用) を再演するリスク

### 2-3. ✗ R. internal_adaptive_atr_breakout (スコア 2)

**即却下理由 (該当基準: 1, 2)**:
- 自身が改修対象とする旧 signal_v2 が **PF 0.95、シャープ -0.39、2年で -385,811 JPY** という撤退原因そのもの
- **スプレッドなし理論値 PF 1.01 → スプレッドで完全に死ぬ** (Pragmatist BT 確定済)
- 改修期待 PF 1.2 の論証が「グリッド試行数 81 + Deflated Sharpe」で更に劣化見込み
- 起草者自身が「ブレイクアウト自体が死んでいる可能性」「同じ轍を踏むリスク」を自認
- G0-A 自己評価が **CONDITIONAL**、worst case で -19,290 JPY 毀損

### 2-4. ✗ I. research_ppo_rl_auxiliary (スコア 2)

**即却下理由 (該当基準: 2, 3)**:
- 論文自身が「**コミッションを入れると Buy & Hold に収束する**」と明示警告 (arXiv 2411.01456)
- 自前 BT 未実施、学習 8-12時間 × ハイパラ 20試行 = 160時間 → 動かしてみないと分からない
- シード依存 ±30%、説明可能性 1/5
- 機会費用 +15-40%(高分散) という記述自体が「銀行の倍率」を語っただけで、PF/Sharpe ベースの実証は皆無
- 起草者自身が「Phase 1 進出は推奨しない」と自認

### 2-5. ✗ K. research_news_sentiment_garch (スコア 2)

**即却下理由 (該当基準: 2, 3)**:
- イベント時スプレッド **2-3pip → 10-20pip (5-10倍)** で「戦略の根幹を脅かす」と起草者自認
- 自前 BT 未実施、年20-30 イベント × 5年 = 100-150 サンプル → 統計信頼性不足
- センチメント-ボラ予測の改善は実証されているが、「ボラ予測 ≠ 方向予測」で取引 PF への翻訳が未証明
- NewsAPI 有料 ($449/月)、GDELT 15分遅延 → コスト負担で機会費用悪化
- 起草者自身が「Phase 1 進出は推奨しない、棚上げ候補」

### 2-6. ✗ Y. internal_loser_pattern_reverse (スコア 2)

**即却下理由 (該当基準: 1, 5)**:
- 起草者自身が「**GBP_JPY 反転 実効 PF ≈ 0.82** (スプレッド込み)、負ける」と自認 (= 撤退基準 PF<0.95 に該当)
- USD_JPY 反転は実取引 7件サンプルで「5年BTで真の反転効果を測ることが必須」= 動かしてみないと分からない
- 起草者自身が「Phase 2 進出非推奨、参考程度」と自認

### 2-7. ✗ G. research_xgboost_walk_forward (スコア 4 → 却下に近い△)

**条件付き却下 (該当基準: 3)**:
- **Quantinsti EUR/USD で赤字** という事実が報告されている (起草者自身が「重く受け止める」)
- 自前 BT 未実施、Triple-Barrier + Meta-Labeling 併用が「必須」だが、それ自体が #M (meta-labeling) で別途検証される
- 機会費用 +15-25% は forextester ベース、自前 FX 実証はゼロ
- 「動かしてみないと分からない」要素が大きい

**理由**: 即却下ライン (スコア 0-2) とは一線を画すが、「自前 BT が無く、既存実証 (Quantinsti) が赤字」で経済性視点では推奨できない。M (meta-labeling) に統合する形で残すのが合理的。

### 2-8. ✗ O. research_volume_profile_microstructure (スコア 4 → 却下に近い△)

**条件付き却下 (該当基準: 3, 4)**:
- 起草者自身が「Tick Volume ≠ 真の出来高」「FX 適用は限定的、futures ほどクリーンでない」「Trending 期で機能しない」と自認
- 自前 BT 未実施、Tick Volume の妥当性検証 (BIS 等の真出来高との相関) も未実施
- 起草者自身が「優先度は低、Phase 1 進出は保留」と自認

---

## 3. TOP 5 推奨 (詳細評価)

### 3-1. TOP 1: A. memory_eur_usd_h1_rsi_pullback

#### スコア: 8/10
**判定**: 採用候補

#### PF 検証
- 提示された PF: **OOS 1.34-1.49** (`data/backtest_grid_h1_EUR_USD.csv`、5年WFA、20パラメータ中 13 が PF>1.0)
- スプレッド込み PF: **1.34-1.49 (込み)** — スプレッド 1.5pip + スリッページ 0.3pip 控除済
- 撤退基準 (PF<0.95) 比較: **✓ 明確に超える**
- signal_v2 比較 (基準 PF 0.95): **1.4-1.6 倍**

#### リスク調整後リターン
- シャープレシオ: Phase 2 で算出予定 (BT グリッドは PF ベース)
- ソルティーノ: 未算出
- MaxDD 想定: -1.4〜-3.8% (BTグリッド平均)、最大 -6.0% / 1.5x 安全係数で -9%

#### 機会費用比較 (100万円口座 × 1年)
| ベンチマーク | 期待 PnL | 候補手法 | 差分 |
|---|---|---|---|
| 銀行預金 (0.05%) | +500 JPY | **+60,000〜+120,000 JPY** | **+59,500〜+119,500** |
| 米国債 (4%) | +40,000 JPY | +60,000〜+120,000 JPY | +20,000〜+80,000 |
| 全世界株 (8%) | +80,000 JPY | +60,000〜+120,000 JPY | -20,000〜+40,000 |

→ **米国債を確実に超え、株式に肉薄。ストレステスト (スプレッド 2x) でも +3〜6% で米国債は維持**

#### 弱点 (経済性視点)
- OOS trades 14-56件/年 = 月 1-5件 → サンプル評価が遅い
- EUR_USD 単一通貨依存 → 通貨分散効かず
- 2024-2026 期間限定、ECB 利上げサイクル終了で構造変化リスク

#### 改善要求
- Deflated Sharpe Ratio の正式算出 (試行数 N=20 × 5 fold で deflation 後 PF 維持を確認)
- 100万円口座 × 1年の期待 PnL JPY 換算は提示済み → 追加要求なし
- Phase 1 BT で 2018-2020 期間 (低ボラ環境) を含むストレステスト

---

### 3-2. TOP 2: B. memory_usd_jpy_m15_rsi_pullback

#### スコア: 8/10
**判定**: 採用候補

#### PF 検証
- 提示された PF: **OOS 1.94-2.46** (`data/backtest_grid_USD_JPY.csv`、5年WFA、20パラメータ中 14 が PF>1.0)
- スプレッド込み PF: **1.94-2.46 (込み)** — ただし M15 のスプレッド負担は H1 より重い (月60件で 90pip = 月-9,000 JPY 固定コスト → 期待値設計済)
- 撤退基準 (PF<0.95) 比較: **✓ 明確に超える**
- signal_v2 比較: **2.0-2.6 倍**

#### リスク調整後リターン
- シャープレシオ: Phase 2 で正式算出 (DSR)
- MaxDD 想定: -10〜-15% (M15高頻度の特性)、1.5x 安全係数で -22%

#### 機会費用比較 (100万円口座 × 1年)
| ベンチマーク | 期待 PnL | 候補手法 | 差分 |
|---|---|---|---|
| 銀行預金 (0.05%) | +500 JPY | **+80,000〜+180,000 JPY** | **+79,500〜+179,500** |
| 米国債 (4%) | +40,000 JPY | +80,000〜+180,000 JPY | +40,000〜+140,000 |
| 全世界株 (8%) | +80,000 JPY | +80,000〜+180,000 JPY | ±0〜+100,000 |

→ **株式並み、上振れシナリオで株式の2倍**

#### 弱点 (経済性視点)
- **OOS trades 11-15 件と少ない**: 統計信頼性が中程度、Deflated Sharpe で慎重判定必須
- **スプレッド負担 大**: 月60件 × 1.5pip = 月-9,000 JPY → PF 2x ストレステストで PF 1.0 ぎりぎりの危険
- 日銀介入リスク (2022/10, 2024/4 の前例で SL ワイドに飛ぶ)
- 亡き者 USD_JPY (H1) で PF 0.48 → M15 で差別化の論証が必要

#### 改善要求
- M15 5年データへの拡張 (現2年) で OOS trades を倍増
- スプレッド 2x ストレステストでの PF を提示
- セッションフィルタの DST 自動対応の実装明示

---

### 3-3. TOP 3: L. research_london_breakout_adaptive

#### スコア: 7/10
**判定**: 採用候補

#### PF 検証
- 提示された PF: **未実施 (自前)、文献 PF 1.2-1.5** (フィルタ追加版、QuantifiedStrategies / forexbee / dailyforex)
- スプレッド込み PF: 未測定。EUR/USD は最低スプレッド (1.0pip) で耐久性高い設計
- 撤退基準 (PF<0.95) 比較: **△ 文献ベースで超える見込み**、自前 BT 必須
- signal_v2 比較: **1.3-1.6 倍 (見込み)**

#### リスク調整後リターン
- シャープレシオ: 未算出 (Phase 1 で実施)
- MaxDD 想定: 10-18%

#### 機会費用比較 (100万円口座 × 1年)
| ベンチマーク | 期待 PnL | 候補手法 | 差分 |
|---|---|---|---|
| 銀行預金 (0.05%) | +500 JPY | **+100,000〜+250,000 JPY** | **+99,500〜+249,500** |
| 米国債 (4%) | +40,000 JPY | +100,000〜+250,000 JPY | +60,000〜+210,000 |
| 全世界株 (8%) | +80,000 JPY | +100,000〜+250,000 JPY | +20,000〜+170,000 |

#### 弱点 (経済性視点)
- **自前 BT 未実施** が最大の弱点
- 「皆が知ってる戦略」の機関投資家逆張りリスク (stop hunt)
- アジアレンジ縮小期 (流動性枯渇) で機能停止

#### 改善要求
- Phase 1 で **5年 EUR/USD H1 自前 BT を最優先実施** (実装最短 1-2 週間)
- スプレッド 1.0pip + 2x ストレステストで PF 1.0 維持確認
- 「皆が知ってる」リスクを Optuna 月次最適化で他者と微妙に異なるパラメータを保つ実装明示

#### 経済性視点の評価コメント
**実装最速 × 検証容易 × 説明可能** の三拍子が揃った候補。文献 PF 1.2-1.5 の信頼性は中程度だが、年取引数 1000+ で統計サンプルが豊富 → 経済性判定が早期に出る。**Phase 1 で最初に検証すべき候補** (起草者推奨と一致)。

---

### 3-4. TOP 4: M. research_meta_labeling_ensemble

#### スコア: 7/10
**判定**: 採用候補

#### PF 検証
- 提示された PF: **未実施 (自前 FX)、文献 Sharpe 0.5→1.2 (Lopez de Prado 2018)、1.4→2.0 (Hudson & Thames)**
- スプレッド込み PF: Secondary Model が敗者除外 → 取引数減 → スプレッド負担軽減 (構造的優位)
- 撤退基準 (PF<0.95) 比較: **△ 文献ベースで超える見込み**、自前 BT 必須
- signal_v2 比較: **Primary が PF 0.8 でも Secondary が False Positive 半減で 1.4+ (理論)**

#### リスク調整後リターン
- シャープレシオ: Hudson & Thames 1.4→2.0 (株式)、FX 適用は未測定
- MaxDD 想定: 8-15% (敗者除外で MaxDD 軽減)

#### 機会費用比較 (100万円口座 × 1年)
| ベンチマーク | 期待 PnL | 候補手法 | 差分 |
|---|---|---|---|
| 銀行預金 (0.05%) | +500 JPY | **+120,000〜+200,000 JPY** | **+119,500〜+199,500** |
| 米国債 (4%) | +40,000 JPY | +120,000〜+200,000 JPY | +80,000〜+160,000 |
| 全世界株 (8%) | +80,000 JPY | +120,000〜+200,000 JPY | +40,000〜+120,000 |

#### 弱点 (経済性視点)
- **自前 BT 未実施** が最大の弱点
- Primary が完全に的外れだと Secondary も救えない (QuantConnect 警告: "not a silver bullet")
- 2段階モデルの維持コスト (Primary と Secondary 両方の監視・再学習)

#### 改善要求
- Phase 1 で **亡き者 MTFPullback を Primary、新規 Secondary で meta-labeling 実装** を最優先
- mlfinpy ライブラリ活用で工数 3週間 → Phase 1 内で実装可能
- Triple-Barrier 設定の感度分析 (profit_take/stop_loss 比) を Optuna で実施

#### 経済性視点の評価コメント
**亡き者の負け要因 (MTFPullback PF 0.81) を Primary として継承し、Secondary が「なぜ負けたか」を学習する設計は反証材料の直接活用 (RETREAT § 「亡き者の挙動データは反証材料として継承」) に最も忠実**。経済性視点では「過去の失敗を構造的に翻訳して将来の収益に変える」唯一の候補。文献の信頼性も最高 (Lopez de Prado 原典、Hudson & Thames 実証)。

---

### 3-5. TOP 5: D. memory_deceased_reversal (EUR_USD 除外版)

#### スコア: 7/10
**判定**: 採用候補 (条件付き)

#### PF 検証
- 提示された PF: **亡き者 DB 直接実証 PF 1.45** (EUR_USD 除外、他5ペア反転、10日間 +4,495 JPY)
- スプレッド込み PF: **1.45 (込み、実取引コスト含む)**
- 撤退基準 (PF<0.95) 比較: **✓ 明確に超える**
- signal_v2 比較: **1.5 倍**

#### リスク調整後リターン
- シャープレシオ: 未算出 (Phase 2 で過去2年シミュレーション必須)
- MaxDD 想定: -10〜-15% (亡き者と対称想定)

#### 機会費用比較 (100万円口座 × 1年)
| ベンチマーク | 期待 PnL | 候補手法 | 差分 |
|---|---|---|---|
| 銀行預金 (0.05%) | +500 JPY | **+135,000 JPY (想定)** | **+134,500** |
| 米国債 (4%) | +40,000 JPY | +135,000 JPY | +95,000 |
| 全世界株 (8%) | +80,000 JPY | +135,000 JPY | +55,000 |

→ 月換算 +13,485 JPY、年率 +13.5% @ 100万 (lot 0.034)

#### 弱点 (経済性視点)
- **OOS 期間が 11日間のみ** → サンプル極小、PF 1.45 の信頼区間極めて広い
- Phase 2 で「過去2年シミュレーション (MTFPullback 順方向を計算し反転)」が必須
- 「亡き者にパラサイト」「データ leakage」批判への耐性が低い (G2-4: 2/5)
- 「亡き者が稀に勝った日 (2026-04-22 +1,389)」の反対側で大負けする尾risk

#### 改善要求
- Phase 1 で **MTFPullback シミュレーション × 反転を 2026-04-21 以前の 2 年** で計算し、PF 1.45 が再現するか確認 (起草者宿題のまま)
- ペア別 enabled flag の運用コスト (Phase 1 内で実装複雑度確認)
- 「亡き者の戦略が市場に再評価されたら反転は退場」という自動停止条件の実装明示

#### 経済性視点の評価コメント
**実数字で PF 1.45 を示せる数少ない候補**。ただし 11日 OOS は信頼性低い。M (meta-labeling) と本質的に同じ「過去の失敗を反証材料として活用」だが、本候補は wrapper 100行で実装最速 (1日)、M は3週間。**Phase 1 で M と並走して BT 実施し、どちらが Phase 2 進出するか比較する形が合理的**。

---

## 4. 全候補レビュー (3-5行)

### 4-1. memory 系 8 件

**A. memory_eur_usd_h1_rsi_pullback (8/10) ◯**
既存 BT グリッド OOS PF 1.34-1.49 を 20 パラメータ中 13 で実証、亡き者 EUR_USD で唯一プラス (+3,315 JPY) と整合。スプレッド込み、5年 WFA 済み。100万円口座で +6〜12%/年 (米国債超え、株式に肉薄)。**Phase 1 進出 強推奨**。

**B. memory_usd_jpy_m15_rsi_pullback (8/10) ◯**
M15 BT グリッド OOS PF 1.94-2.46 を 20 パラメータ中 14 で実証。H1 では PF>1.0 がゼロという timeframe 特異性が定量確認済み。OOS trades 11-15 件と少ないのが懸念だが、+8〜18%/年で株式並み。**Phase 1 進出 推奨、要 Deflated Sharpe**。

**C. memory_mfi_adx_breakout (6/10) △**
@onlybreakouts 実例 ($87K→$200K) + 既存 RSI BT 平均 PF 1.06 からの上振れ論証で「理論的 PASS」だが、**実 BT 未実施**。クロスペア生存基準 (6ペア中 4/6 PF>1.2) は強力だが、FX 適用の経済性は仮説段階。Phase 1 で 6ペア × 270 構成 × 5 fold = 1350 試行の自前 BT が必須。

**D. memory_deceased_reversal (7/10) △ → 採用候補**
亡き者 DB 64件から計算した実数字 PF 1.45 (EUR_USD 除外版) は他候補の「想定」より信頼性高。ただし OOS 11日は極小。+13〜20%/年想定。**条件付き Phase 1 進出**: 過去2年 MTFPullback シミュレーションで PF 1.45 が再現できれば Phase 2。

**E. memory_seasonal_regime_gate (6/10) △**
ベース戦略 (EUR_USD H1 RSI PF 1.4) + SeasonalDetector フィルタ。シナリオ A (PF 1.7-2.0) / B (PF 1.5) / C (PF 0.9 で自動 OFF) のうち A 限定で機会費用超え。**ベース戦略 (A候補) で既に PF 1.4 が出ている時点で、フィルタ追加価値が限定的**。Phase 2 で A と並走比較する形が合理的。

**F. memory_gbp_jpy_m15_high_pf_caution (0/10) ✗**
**即却下**。OOS trades 4件で PF 7.38 は統計的に無意味、起草者自身が「年 +800 JPY @ 100万 = 銀行預金以下」と試算。「BT で好成績、実取引で機会喪失」の典型。

**V. memory_llm_filter_dual_validation (5/10) △**
ベース戦略 (A候補) PF 1.4 + LLM フィルタで PF 1.7-1.9 想定だが、**LLM 過去 BT 不可能**。ペーパートレード 3ヶ月必須。コスト月100 JPY は無視可。「動かしてみないと分からない」要素が経済性視点で減点。**Phase 3 オプションとして A の上に乗せる形が合理的** (MECE_AUDIT.md 推奨と一致)。

**W. memory_multi_strategy_portfolio (4/10) △ Phase 4 案件**
個別戦略 (A: PF 1.34-1.49 + B: PF 1.94-2.46) を 50/50 で並走、リスクパリティで月次再配分。想定 PF 1.5-1.8、+8〜15%/年。**前提条件: A と B が Phase 2 通過**。本提案単独は Phase 4 案件、Phase 1-2 査読では「保留トレー」。スコア 4 は前提条件依存の減点。

### 4-2. research 系 9 件

**G. research_xgboost_walk_forward (4/10) ✗ 条件付き却下**
Quantinsti EUR/USD で **赤字** という事実が報告、自前 BT 未実施。forextester (PF 1.6) は別実装。Triple-Barrier + Meta-Labeling 必須なら、それ自体は M (meta-labeling) で別途検証される。M に統合する形で残すのが合理的。

**H. research_hmm_regime_ensemble (5/10) △**
Quantinsti BTC で Sharpe 1.76 実証だが **FX 未検証**。D1 タイムフレームで月数取引 → サンプル少。+10-18%/年想定だが、亡き者 GBP_JPY 短期保有との不整合あり (起草者自認)。Phase 1 で USD_JPY D1 5年 自前 BT 必須。

**I. research_ppo_rl_auxiliary (2/10) ✗ 即却下**
論文自身が「コミッション込みで Buy & Hold に収束する」と警告。学習 8-12時間 × 160時間ハイパラ探索 → 動かしてみないと分からない。期待値 +15-40% は高分散すぎ。説明可能性 1/5 で人間レビュー不能。起草者自身が「Phase 1 進出非推奨」。

**J. research_cointegration_pairs (6/10) △**
文献 PF 1.3-2.0 (Engle-Granger 以来50年実証)、方向中立で他戦略と低相関 (G2-2 満点)。**自前 FX BT 未実施** が最大の弱点。SNB 2015 のような関係崩壊リスクあり。+8-15%/年想定。**TOP 5 圏外だが分散源としては優秀**、Phase 1 で 6 通貨ペア × WFA 16サイクル 実施推奨。

**K. research_news_sentiment_garch (2/10) ✗ 即却下**
イベント時スプレッド 5-10倍拡大が致命、NewsAPI $449/月 (有料) or GDELT 15分遅延 → コスト負担で機会費用悪化。方向予測 ≠ ボラ予測の翻訳が未証明。

**L. research_london_breakout_adaptive (7/10) ◯ TOP 3**
文献 PF 1.2-1.5、実装 1-2 週間で最速、年取引数 1000+ で統計信頼性高。EUR/USD スプレッド 1.0pip で耐久性最高。+10-25%/年想定。**Phase 1 で最初に検証すべき候補**。

**M. research_meta_labeling_ensemble (7/10) ◯ TOP 4**
Lopez de Prado 原典 + Hudson & Thames Sharpe 1.4→2.0、亡き者 MTFPullback を Primary 流用で反証材料直接活用。**自前 FX BT 未実施** が弱点だが mlfinpy 活用で3週間。+12-20%/年想定。

**N. research_carry_trade_systematic (5/10) △**
50年実証 Sharpe 0.3-0.5、Macrosynergy で VIX フィルタ追加で Sharpe 1.29 達成。**自前 BT 未実施**、2024-2026 米日金利差縮小で USD/JPY キャリー弱化、AUD/JPY 中心の再設計が必要。+6-12%/年想定で米国債並み。テールリスク (2008/2015/2020) 大。

**O. research_volume_profile_microstructure (4/10) ✗ 条件付き却下**
Tick Volume ≠ 真の出来高 (FX OTC 構造の限界)、Trending 期で機能しない、起草者自身が「優先度低、Phase 1 進出保留」と自認。Phase 1 進出の優先度は確実に L/M/J より低い。

### 4-3. internal 系 9 件 (補強含む)

**P. internal_eurusd_meanrev_focus (5/10) △**
BollingerReversal (素の PF 1.24) + H1 トレンドフィルタ + セッション制限 + タイムストップで PF 1.4 目標。**改善3点の効果未検証**、亡き者 EUR_USD 13件 (PF 2.37) を cherry-pick とする批判受ける (G2-4: 3/5)。Phase 1 で改善版 BT 必須。**A と本質的に類似 (EUR_USD MR)** で Phase 2 で並走比較。

**Q. internal_confluence_gate_filter (6/10) △**
既存 ConvictionScorer (5指標) を「2点が4つ以上」厳格化。実装最低工数 (1-2週間)、亡き者 NULL 問題直接修正。**ただし期待 PnL +24,000〜+45,000/年 = 米国債並み**で経済性ボーダーライン。発火頻度 1/5 で取引数 30/年 程度→絶対額不足。MECE_AUDIT 統合案 (Q+Q2+V → Q) の代表候補。

**Q2. internal_bull_bear_dialectic (4/10) △**
BearResearcher (5チェック) を直列ゲート化。**期待 +40,000〜+60,000/年 = 米国債並み止まり**、Q と相関高い (G2-2: 3/5)、構造的に Q と同質。MECE 統合で Q に吸収推奨。

**R. internal_adaptive_atr_breakout (2/10) ✗ 即却下**
signal_v2 (撤退原因 PF 0.95) の改修版、worst case で -19,290 JPY 毀損。起草者自身が「ブレイクアウト自体が死んでいる可能性」「Phase 1 BT で PF<1.0 のままなら即廃案」と自認。

**S. internal_long_trend_following (0/10) ✗ 即却下**
**起草者自身が実 BT で 3ペア合算 PF 0.96、5年累計 -1,593 JPY を実証**し、案 B (却下、MECE 補強の役割は果たした) を自己推薦。経済性視点で完全に同意。

**T. internal_yz_vol_regime_router (5/10) △**
SeasonalDetector を「フィルター」ではなく「戦略ルーター」として再利用。LOW_VOL 単独で BollingerReversal PF 1.24、HIGH_VOL モメンタム部分が **未 BT**。+15-25万/年想定。ULTRA 三重定義罠の再演リスク (G2-4: 3/5)、E と T は SeasonalDetector の異なる活用法で**重複ぎみ**。

**U. internal_session_split_strategies (5/10) △**
セッション境界強制クローズ + ニュース回避で跨ぎリスク排除。**3戦略×4セッション×5fold = 81 試行で過剰最適化リスク**、サンプル過少懸念。+6〜9万/年想定で米国債超え程度。経済カレンダー API 新規依存で外部障害ポイント増。

**X. internal_dynamic_portfolio_weighting (4/10) △ Phase 4 案件**
Multiplicative Weights Update で複数戦略の動的重み。**前提条件: 個別戦略 (BR/MTF/Confluence 等) の Phase 2 通過**。本提案単独は Phase 4 案件、Phase 1-2 査読では「保留トレー」。W との重複 (粒度) はあるが本提案は N 戦略動的 vs W は 2戦略固定で差別化。

**Y. internal_loser_pattern_reverse (2/10) ✗ 即却下**
起草者自身が「GBP_JPY 反転 実効 PF ≈ 0.82 (スプレッド込み)、負ける」と試算済み。USD_JPY 7件サンプルでは反転仮説の検証は不能。

---

## 5. 経済性視点の総括

### 5-1. 構造観察

#### 観察 1: 「実証」と「期待」の二極化

26 候補のうち **自前 BT で PF を実証している (= 経済性 G0-A を満たすと自信を持って言える) のは 4 候補のみ**:

| 候補 | 実証 PF | 出典 |
|---|---|---|
| A. eur_usd_h1_rsi_pullback | OOS 1.34-1.49 | `backtest_grid_h1_EUR_USD.csv` |
| B. usd_jpy_m15_rsi_pullback | OOS 1.94-2.46 | `backtest_grid_USD_JPY.csv` |
| D. deceased_reversal (EUR_USD 除外) | 1.45 (10日実取引) | `fx_trading_prod_snapshot.db` 反転計算 |
| F. gbp_jpy_m15 (失敗側) | OOS 7.38 但 trades=4 | `backtest_grid_GBP_JPY.csv` |
| S. long_trend_following (失敗側) | 0.96 (3ペア合算) | `_donchian_bt.py` 自己 BT |

**F と S は両方とも「実証されたが却下」(F は trades 過少 = 銀行以下、S は PF<0.95)** → 実証ベースでの採用候補は **A/B/D の 3 件のみ**。

#### 観察 2: 平均回帰 10/24 (42%) の過剰集中は経済性視点でも独立検証で確認

平均回帰候補が 10/24 (MECE_AUDIT § 1) で集中している点を経済性視点で独立検証:

- 10 候補の経済性スコア中央値: 5
- 10 候補のうち実証 PF 提示: A (1.34-1.49), B (1.94-2.46), D (1.45), F (7.38=却下), P (1.24=BR), の 5 件
- **平均回帰の集中が「亡き者 EUR_USD PF 2.37」の引力に依存している**ことを経済性視点でも確認 (PROPOSAL_REVIEW 観察)
- A/B/D の 3 件は実証ベースで採用候補だが、**EUR_USD の MR 一極集中リスク**は経済性的にも警告
- → **L (London Breakout BO 系) と M (Meta-Labeling) を Phase 1 に含めることで戦略タイプ多様化を確保**

#### 観察 3: 「機会費用論証の欠落 / 米国債並み止まり」候補が想定以上に多い

経済性 G1-6 (機会費用 +5,000 JPY/年以上) を満たさないか、米国債 (+40,000) と同等止まりの候補:

| 候補 | 問題 |
|---|---|
| **F. gbp_jpy_m15_high_pf_caution** | +800 JPY/年 = 銀行預金以下 ✗ |
| **S. long_trend_following (3ペア)** | -1,593 JPY/年 = 銀行以下 ✗ |
| **Q. confluence_gate_filter** | +24,000〜+45,000 = 米国債並み △ |
| **Q2. bull_bear_dialectic** | +40,000〜+60,000 = 米国債並み △ |
| **N. carry_trade** | +60,000〜+120,000 = 米国債超え程度 |
| **U. session_split** | +60,000〜+90,000 = 米国債超え程度 |

「Q/Q2 = 米国債並み止まり」は経済性視点で **致命的弱点**。撤退教訓 RETREAT § 「数百万運用して年間数千円なら銀行のほうがマシ」を Phase 0 の段階で再演する。MECE_AUDIT 統合案 (Q+Q2 → Q) と組み合わせると **Q1 (Q) は採点ボーダー、Q2 は統合先候補**。

#### 観察 4: 補強候補 internal_long_trend_following は起草者自身が PF 0.96 で却下推奨を明示、経済性視点でも独立に却下を確認

S. internal_long_trend_following は MECE_AUDIT の C 違反補強として起草され、本人自己評価 **「Gate 0 FAIL、案 B 却下推奨」**:
- 3ペア合算 PF 0.96 = signal_v2 と同水準
- 5年累計 -1,593 JPY = 銀行預金以下
- USD_JPY 単独運用案 (PF 1.74) は cherry-pick 救済、起草者自身が「他の高 PF 候補 (A, B) に劣後」と認識

**本査読の経済性視点でも完全に同意 → 即却下**。MECE 補強の役割は「平均回帰偏重」の認識を委員間で共有した時点で達成。Phase 1 BT 工数を割く優位性なし。

### 5-2. Phase 1 進出推奨リスト (経済性視点)

| 優先度 | 候補 | スコア | 工数 | 理由 |
|---|---|---|---|---|
| 1 | A. eur_usd_h1_rsi_pullback | 8 | 1-2日 | 実証 PF 1.34-1.49、亡き者整合、最速 |
| 2 | B. usd_jpy_m15_rsi_pullback | 8 | 1-2日 | 実証 PF 1.94-2.46、A と相関低 |
| 3 | L. london_breakout_adaptive | 7 | 1-2週 | 文献 PF 1.2-1.5、年取引 1000+、戦略タイプ多様化 (BO) |
| 4 | M. meta_labeling_ensemble | 7 | 3週 | 文献 Sharpe 1.4→2.0、亡き者 MTFPullback 反証材料活用 |
| 5 | J. cointegration_pairs | 6 | 2週 | 文献 PF 1.3-2.0、方向中立 (相関分散源 G2-2 満点) |
| 6 | D. deceased_reversal (EUR_USD 除外) | 7 | 1日 | 実数字 PF 1.45 (但 OOS 11日)、Phase 1 で過去2年シミュ |

合計 6 件で経済性視点の Phase 1 進出を推奨。MECE_AUDIT の Phase 2 進出推奨数 (6-10 件) と整合。

### 5-3. 即却下リスト (経済性視点) 8 件

1. **F. gbp_jpy_m15_high_pf_caution** (基準 5: 年 +800 JPY = 銀行以下)
2. **S. long_trend_following** (基準 1, 5: 起草者自身が PF 0.96 / 銀行以下を実証)
3. **R. adaptive_atr_breakout** (基準 1, 2: signal_v2 PF 0.95 + スプレッドで死亡)
4. **I. ppo_rl_auxiliary** (基準 2, 3: コミッション収束 + 動かしてみないと分からない)
5. **K. news_sentiment_garch** (基準 2, 3: スプレッド 5-10倍 + 自前 BT 未実施)
6. **Y. loser_pattern_reverse** (基準 1, 5: GBP_JPY 反転 PF 0.82)
7. **G. xgboost_walk_forward** (基準 3: Quantinsti EUR/USD 赤字事例、M に統合)
8. **O. volume_profile_microstructure** (基準 3, 4: Tick Volume 妥当性未検証 + 起草者自認の優先度低)

### 5-4. 経済性視点での1行サマリ

> **26 候補のうち、自前 BT で「PF>0.95 + 機会費用 (米国債 4%) 超え + スプレッド込み」の3条件を実証しているのは A/B/D の 3 件のみ。L/M/J を文献ベースで追加し、6 件で Phase 1 を回すのが経済性視点での最終推奨。他は全て「未 BT」「期待」「想定」止まりで、PROPOSAL_TEMPLATE G0-A の経済性 Gate を厳格に適用すると 18/26 が条件付き △ または ✗ に落ちる。**

> **撤退教訓 RETREAT § バグ③「経済性 Gate 不在」を Phase 0 で再演しないために、本査読は経済性視点一本で 26 候補を絞った。Phase 1 で実際に動かして PF と機会費用の数字を出すべきは最大でも 6 件、最小では A/B の 2 件で十分。**

---

## 6. 査読メタ — 経済性視点の限界と注意

### 6-1. 経済性視点の限界

1. **戦略タイプ多様性は他視点に委ねる**: 本査読は PF / Sharpe / 機会費用一本で評価しており、戦略タイプの多様化 (MR 偏重の修正) は MECE_AUDIT と他の評価委員 (構造視点) に委ねる
2. **Phase 4 案件 (W, X) は前提条件依存で減点したが、個別戦略が確定すれば再評価可**
3. **「想定」と「実証」の二極化評価**は経済性視点では正しいが、保守的すぎて将来性のある候補 (M meta-labeling 等) を不当に減点した可能性
4. **5年 BT のみで判断**は CTA (S) のような 10-30年スパンで生存する性質の戦略には不利 — ただし S は起草者自身も 5年で却下推奨なので問題なし

### 6-2. 査読確信度マトリックス

| 結論 | 確信度 | 根拠 |
|---|---|---|
| F, S の即却下 | **極めて高** | 起草者自身が自己 BT で銀行以下を実証、自己却下推奨 |
| A, B の TOP 推奨 | **極めて高** | 実 BT グリッドで PF 1.34-2.46 実証、亡き者整合 |
| I, K の即却下 | **高** | コミッション収束 / スプレッド致命の構造欠陥 |
| R, Y の即却下 | **高** | 起草者自身が PF<0.95 を自認 |
| L, M, D の TOP 推奨 | **中-高** | 文献ベース、自前 BT は未実施だが信頼性ある実証あり |
| Q/Q2 の米国債並み判定 | **中** | 起草者自身が「機会費用劣後」を自認、本査読も同意 |
| G, O の条件付き却下 | **中** | 即却下ライン (スコア 0-2) と一線、M/J に統合する形で残せる |

---

**査読終了。**

総合所見: **経済性 Gate を厳格に通すと 6 件、最小 2 件 (A/B) で Phase 1 を回すのが合理的。「実証ベース」「機会費用 (米国債 4%) 超え」「スプレッド込み」の3条件を満たさない候補に Phase 1 BT 工数を割くのは、撤退教訓 § バグ③ の再演リスク**。
