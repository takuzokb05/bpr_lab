# Phase 0 候補 MECE 監査レポート

**監査日**: 2026-05-26
**監査者**: ultrathink-debugger (sub-agent)
**対象**: `docs/proposals/phase0/` 内 24 候補 (memory 8 / research 9 / internal 7)
**目的**: 6 評価委員による査読前の MECE (Mutually Exclusive, Collectively Exhaustive) チェック

---

## エグゼクティブサマリ (先に結論)

| 観点 | 結果 |
|---|---|
| **M 違反 (重複)** | **5 組の構造的重複**を検出。3 組は統合推奨、2 組は差分残し |
| **C 違反 (欠落)** | **3 カテゴリ欠落**。うち 1 つ (トレンドフォロー × 適応的閾値) は Phase 0 で補強推奨、残り 2 つは意図的除外で OK |
| **粒度の不揃い** | **3 候補がポートフォリオ階層**で他と異なるレイヤー。Phase 4 案件として分離推奨 |
| **推奨候補数 (查読対象)** | **24 → 18 候補** に削減 (重複統合 -3、ポートフォリオ層分離 -3、補強提案 +0 = 純減 6 ※下記詳述) |

**推奨方針**: 「**18 候補を 6 評価委員で並列査読** + **3 ポートフォリオ層候補を Phase 4 案件として保留トレー入り**」

ただし「全 24 を並走で査読する」選択肢も合理的。重複と判定したペアでも自己改善メカニズムや撤退条件の細部に差分があり、6 委員に「**MECE 統合せず 24 のまま見るが、本監査の M/C 違反タグを参照しつつ評価せよ**」と指示するのが最も情報損失が少ない (この論証は §6.B に展開)。

---

## 1. 24 候補マッピングマトリックス

各候補の戦略タイプ・シグナル源・自己改善方式・通貨/TF・既存資産再利用度・リスク管理・自己採点を横断比較。

### 凡例
- **戦略タイプ**: MR=平均回帰, BO=ブレイクアウト, TR=トレンドフォロー, ML=機械学習, STAT=統計的裁定, CARRY=キャリー, EVENT=イベントドリブン, **PF**=ポートフォリオ層 (上位レイヤー)
- **シグナル源**: TA=テクニカル指標, PA=価格パターン, VOL=ボラ, VOLM=出来高, REG=レジーム判定, MLP=ML予測, NEWS=ニュース・センチメント, RATE=金利差, MULTI=マルチ戦略合成
- **自己改善**: RR=ローリング再学習, BO_=ベイズ最適化, OL=オンライン学習, RL=強化学習, HMM=HMM レジーム, NONE=なし
- **再利用度**: 高/中/低
- **PF claim**: 自己採点での主張 PF (実証/期待)

| # | ファイル名 (短縮) | 戦略タイプ | シグナル源 | 自己改善 | 通貨/TF | 再利用度 | PF claim | 採点 |
|---|---|---|---|---|---|---|---|---|
| 1 | memory_eur_usd_h1_rsi_pullback | MR | TA (RSI+ATR+EMA) | RR月次 + BO_ | EUR_USD H1 | 高 | 実証 1.34-1.49 OOS | 87 |
| 2 | memory_usd_jpy_m15_rsi_pullback | MR | TA (RSI+ATR+EMA) + Session | RR週次 + BO_ | USD_JPY M15 | 高 | 実証 1.94-2.46 OOS | 79 |
| 3 | memory_mfi_adx_breakout | BO | TA (ADX+MFI+ATR+breakout) | RR四半期 + LLM推薦 | 6ペア H1 | 中 | 理論 1.3-1.7 | 77 |
| 4 | memory_deceased_reversal | MR (反転) | 既存戦略の逆方向 | RR月次 + 仮想モニタ | 5ペア M15/H1 | 高 | BTで 1.23 (1.45 除外時) | 70 |
| 5 | memory_llm_filter_dual_validation | MR + LLM フィルタ | TA + NEWS (LLM) | RR月次 + プロンプト改訂 | EUR_USD H1 | 中 | ベース 1.4 + LLM=1.7-1.9 | 77 |
| 6 | memory_seasonal_regime_gate | MR + REG フィルタ | TA + VOL (YZ_vol) | RR四半期 + on/off 自動 | EUR_USD H1+M15 | 中 | ベース 1.4 + 上振れ 1.7-2.0 | 72 |
| 7 | memory_gbp_jpy_m15_high_pf_caution | MR | TA (RSI+ATR+EMA) | RR月次 | GBP_JPY M15 | 高 | BT 7.38 (但OOS 4件) | 51 |
| 8 | memory_multi_strategy_portfolio | **PF** | MULTI (#1 + #2 合成) | RR月次 + リスクパリティ | EUR_USD H1 + USD_JPY M15 | 高 | 1.5-1.8 想定 | 85 |
| 9 | research_xgboost_walk_forward | ML | MLP (XGBoost 32特徴量) | RR月次 + BO_ (Optuna) | EUR_USD/USD_JPY H1 | 中 | 1.3-1.6 文献 | 76 |
| 10 | research_hmm_regime_ensemble | ML + REG | REG (HMM 3状態) + MLP (RF) | RR月次 + HMM 自体 | USD_JPY D1 | 中 | 1.4 想定 | 77 |
| 11 | research_ppo_rl_auxiliary | ML | RL (PPO+Aux) | RL継続学習 | EUR_USD/USD_JPY H1 | 低 | 1.1-1.3 想定 | 55 |
| 12 | research_cointegration_pairs | STAT | PA (z-score on spread) + REG | RR週次 + BO_ | EUR-GBP, AUD-NZD 等 H1 | 低 | 1.3-2.0 文献 | 82 |
| 13 | research_news_sentiment_garch | EVENT | NEWS (BERT) + VOL (GARCH) | RR月次 + モデル比較 | USD_JPY 等 H1 | 低 | 1.1-1.3 想定 | 56 |
| 14 | research_london_breakout_adaptive | BO | PA (range break) + TA filter | RR月次 + BO_ (Optuna) | EUR_USD/GBP_USD H1 | 低 | 1.2-1.5 文献 | 82 |
| 15 | research_meta_labeling_ensemble | ML (フィルタ) | TA (Primary) + MLP (Secondary RF) | RR月次 + BO_ (Purged KF) | USD_JPY 5ペア H1/H4 | 中 | 1.3-1.5 想定 | 85 |
| 16 | research_carry_trade_systematic | CARRY | RATE + REG (VIX/DXYフィルタ) | RR四半期 + BO_ | AUD/JPY, NZD/JPY 等 D1 | 低 | 1.3-1.7 文献 | 75 |
| 17 | research_volume_profile_microstructure | MR | VOLM (POC/VA edge) + TA | RR月次 + BO_ | EUR_USD M5+H1 | 低 | 1.2-1.5 想定 | 67 |
| 18 | internal_eurusd_meanrev_focus | MR | TA (BB+RSI+EMA+ADX+Session) | RR月次 + KL Div | EUR_USD M15 | 高 | 実証 1.24 (素) → 1.4 目標 | 74 |
| 19 | internal_yz_vol_regime_router | MR + BO ルーティング | REG (YZ_vol) → 戦略選択 | RR月次 + on/off | 主要ペア M15 | 高 | LOW_VOL 1.24, 上振れ 1.4 | 76 |
| 20 | internal_confluence_gate_filter | MR/TR + コンフルゲート | TA 5指標一致 | RR月次 + N値感度 | EUR_USD M15 | 高 | ベース 1.24 → 1.5 想定 | 77 |
| 21 | internal_bull_bear_dialectic | MR/TR + 反対論ゲート | TA + 5チェック severity | RR月次 + 重み校正 | EUR_USD M15 | 高 | ベース 1.24 → 1.5 想定 | 76 |
| 22 | internal_adaptive_atr_breakout | BO | PA (ATR breakout) + REG (ADX) | RR月次 + cooldown | 3ペア M15 | 高 (旧 signal_v2 流用) | 旧 0.95 → 1.2 目標 | 66 |
| 23 | internal_session_split_strategies | MR + BO + EVENT 回避 | Session 別戦略 + NEWS 回避 | RR月次 + ニュースAPI FB | 3ペア M15 | 高 | ベース 1.24/2.05 → 1.5-1.8 | 75 |
| 24 | internal_loser_pattern_reverse | MR (反転) | 既存 MA crossover の逆方向 | RR月次 + 仮説検証 | GBP_JPY/USD_JPY M15 | 高 | USD_JPY 実効 1.48 想定 | 57 |
| 25 | internal_dynamic_portfolio_weighting | **PF** | MULTI 動的重み (MWUM) | OL毎日 + 戦略入れ替え | 全戦略合成 | 低 (個別戦略前提) | 1.4-1.8 想定 | 79 |

> 注: 表で 24 でなく 25 になっているのは、`memory_multi_strategy_portfolio` (#8) と `internal_dynamic_portfolio_weighting` (#25) を別個に並べているため。両者ともポートフォリオ層 (粒度の不揃い対象) → §4 参照。実際の候補ファイル数は 24。

### マトリックスの観察

**戦略タイプ分布**:
| タイプ | 数 | 候補 # |
|---|---|---|
| MR (平均回帰) | 10 | 1, 2, 4, 5, 6, 7, 17, 18, 19, 21 (※19 は LOW_VOL 側) |
| BO (ブレイクアウト) | 4 | 3, 14, 22, 19 (HIGH_VOL 側) |
| ML (機械学習) | 4 | 9, 10, 11, 15 |
| STAT (統計裁定) | 1 | 12 |
| CARRY (キャリー) | 1 | 16 |
| EVENT (イベント) | 1 | 13 |
| PF (ポートフォリオ層) | 2 | 8, 25 |
| ハイブリッド/ゲート | 4 | 20 (コンフル), 21 (Bear), 23 (Session割当), 6 (Seasonal) |

→ **平均回帰過剰** (10/24 = 42%) が顕著。これは亡き者 EUR_USD PF 2.37 の引力に集中している。

---

## 2. M 違反 (重複) の検出と統合提案

### M 違反組 ① (実質同じ): 「ベース戦略 + 既存ゲート機構」3 組
**候補 #5 (LLM Filter), #20 (Confluence Gate), #21 (Bull/Bear Dialectic)**

- **共通構造**: いずれも「**ベース戦略 (EUR_USD H1 RSI Pullback or BollingerReversal) を温存しつつ、上位ゲートを追加して悪取引を除外する**」設計
- **シグナル源の重複**: 全て TA (RSI/ATR/EMA) ベース、ゲート機構だけが異なる (LLM verdict / 5指標コンフル / 5チェック severity)
- **自己改善方式**: いずれも「**月次 RR + ゲート閾値の再最適化**」で構造的に同じ
- **ベースPF claim**: 全て「ベース 1.24-1.4 → ゲート効果で 1.5-1.9 想定」で重なる

**差分**:
- #5: ゲート手段が**外部 LLM API** (Claude/GPT 二段検証) → コスト発生・過去BT不可
- #20: ゲートが**5指標一致カウント**で純内部 → 過去BT可能
- #21: ゲートが**Bear severity (5 check) ペナルティ** → 過去BTやや困難

**判定**: **実質同じカテゴリ (= ベース戦略 + フィルタ強化)**。差分は「フィルタ手段の違い」にすぎず、Phase 1 で 3 並列 BT する価値が薄い。

**統合提案**:
- **代表候補**: `internal_confluence_gate_filter` (#20) を残す (最も実装容易・自己BT可能・採点 77 で中庸)
- **マージ要素**:
  - #21 の「**反対論カウントメカニズム**」を #20 の Confluence 内に組み込み (5指標一致だけでなく、Bear severity も並列カウント)
  - #5 の「**LLM フィルタ**」は **後段の Phase 3 オプション** として別管理 (BT困難な性質ゆえ、Phase 1 ではなく Phase 3 でペーパー実測で評価する別工程)

→ **3 候補 → 1 候補 + Phase 3 オプション 1 件**。**純減 2 候補**。

---

### M 違反組 ② (実質同じ): 「亡き者 MA crossover を反転」2 組
**候補 #4 (Deceased Reversal), #24 (Loser Pattern Reverse)**

- **共通構造**: 亡き者の MA crossover 系シグナル (#4 = MTFPullback wrapper / #24 = OldMACrossover) **を実取引データに基づき逆方向で発火**
- **シグナル源**: 完全に同じ (亡き者シグナル + 反転 wrapper)
- **エッジ源根拠**: 両方とも「亡き者 PF 0.81」を反転して使う仮説、adverse selection / Barber & Odean 2000 同種引用
- **対象ペア**: ほぼ同じ (GBP_JPY/USD_JPY を主に反転対象、EUR_USD は除外)

**差分**:
- #4: 亡き者の **MTFPullback 系全シグナル**を反転、EUR_USD は順方向継続
- #24: 亡き者の **MA crossover** に絞り、GBP_JPY/USD_JPY 限定

**判定**: **実質同じ構造**。#24 の方が対象を絞っているが、これは #4 内の EUR_USD 例外と表裏一体の議論。

**統合提案**:
- **代表候補**: `memory_deceased_reversal` (#4) を残す (採点 70 vs 57、自己改善設計がより精緻)
- **マージ要素**: #24 の「**反転仮説そのものの月次自己検証** (反転 PF vs 順方向 PF を並走計測、2 回連続で反転敗北なら全廃案)」 を #4 に組み込む。これは #4 にも記載があるが #24 の方が明示的。

→ **2 候補 → 1 候補**。**純減 1 候補**。

---

### M 違反組 ③ (微妙に違う、差分残し推奨): 「平均回帰戦略 EUR_USD H1/M15 ベース」
**候補 #1 (memory_eur_usd_h1_rsi_pullback), #18 (internal_eurusd_meanrev_focus)**

- **共通**: EUR_USD 単一通貨、平均回帰系、亡き者 EUR_USD PF 2.37 を根拠とする
- **シグナル源**: #1 = RSI + ATR + EMA Pullback / #18 = Bollinger + RSI + ADX + EMA + Session filter
- **TF**: #1 = **H1** / #18 = **M15**
- **採点根拠**: #1 は既存 BT グリッド `backtest_grid_h1_EUR_USD.csv` で **OOS PF 1.34-1.49 実証** / #18 は `bollinger_reversal.py` の **PF 1.24 (M15) 実証**

**差分**:
- TF が H1 vs M15 で **異なる時間軸 → 取引頻度・シグナル数・スプレッド負担が桁違い**
- シグナル本体が RSI Pullback vs Bollinger Reversal で別物 (両方とも実証済)
- セッションフィルタの有無

**判定**: **全く違う** (実装が共存しても干渉せず、両者とも独立して PF>1.0 を実証している)。

**統合提案**: **両者残し**。MECE 上問題なし。

---

### M 違反組 ④ (微妙に違う、差分残し推奨): 「ブレイクアウト系」
**候補 #3 (MFI+ADX Breakout), #14 (London Breakout), #22 (Adaptive ATR Breakout)**

- **共通**: 全て BO (ブレイクアウト) タイプ
- **差分**:
  - #3: **6ペアクロスバリデーション** + MFI/ADX フィルタ + H1
  - #14: **セッション (アジアレンジ)** を利用した **時間構造的非効率** + EUR_USD/GBP_USD 中心
  - #22: **ATR breakout の改修版** (亡き者の signal_v2 PF 0.95 を改善) + ADX レジームフィルタ

**判定**: **エッジ源が完全に異なる** (#3 は MFI フィルタ強化 / #14 はセッション時間軸 / #22 は亡き者改修)。**全部残し**で MECE OK。

ただし注意: #22 (Adaptive ATR Breakout) は「亡き者で失敗した仕様の改修」という性質上、`feedback-deceased-world-data-inheritance` 警告に最も近い。**Phase 1 BT で PF>1.2 不達成なら即廃案**を撤退条件として明記済。

---

### M 違反組 ⑤ (微妙に違う、差分残し推奨): 「ML フィルタ系」
**候補 #9 (XGBoost WFO), #15 (Meta-Labeling Ensemble)**

- **共通**: ML 機械学習で TA 特徴量を入力、WFO で再学習
- **差分**:
  - #9: **XGBoost が直接 BUY/SELL/FLAT を予測** (3値分類器)
  - #15: **Primary 戦略 (SMA cross 等) を Secondary が取捨選択** (フィルタ用途)

**判定**: 構造的に異なる (直接予測 vs フィルタ予測)。Lopez de Prado 2017 が #9 を否定する理論的論証あり (= meta-labeling は side と size を分離するから優位)。

**統合提案**: **両者残し**。むしろ Phase 1 BT で「直接予測 vs フィルタ予測」のどちらが PF を出すかを比較するメタ実験になる。

---

### M 違反組 ⑥ (実質同じ、ポートフォリオ層): **#8 と #25**
**候補 #8 (memory_multi_strategy_portfolio), #25 (internal_dynamic_portfolio_weighting)**

- **共通構造**: 複数戦略の合成 → ポートフォリオ層 (上位レイヤー)
- **差分**:
  - #8: **2 戦略固定** (EUR_USD H1 RSI + USD_JPY M15 RSI) + **月次リスクパリティ**
  - #25: **N 戦略動的** (3-7戦略を維持) + **毎日 MWUM 重み更新** + 戦略入れ替え

**判定**: **構造的に同じ (ポートフォリオ層)** が、**粒度** が異なる (固定 vs 動的)。**両者とも個別単独戦略の Phase 2 通過が前提条件**。

→ §4 (粒度の不揃い) で扱う。**統合せず、Phase 4 保留トレーへ移送**。

---

### M 違反の統合まとめ

| 違反組 | 判定 | アクション | 純減 |
|---|---|---|---|
| ① #5 + #20 + #21 (フィルタ強化) | 実質同じ | #20 に統合、#5 は Phase 3 オプション化 | **-2** |
| ② #4 + #24 (亡き者反転) | 実質同じ | #4 に統合 | **-1** |
| ③ #1 + #18 (EUR_USD MR) | 全く違う | 両者残し | 0 |
| ④ #3 + #14 + #22 (Breakout) | 全く違う | 全部残し | 0 |
| ⑤ #9 + #15 (ML) | 微妙に違う | 両者残し (比較実験価値) | 0 |
| ⑥ #8 + #25 (Portfolio) | 粒度差 | §4 で扱う | (-3) |

**M 違反処理 = 純減 3 候補** (フィルタ統合 -2、反転統合 -1)

---

## 3. C 違反 (欠落) の検出と補強提案

### 検査軸: 戦略タイプ × シグナル源 × 自己改善 × 通貨/TF

評価項目 (A-F 軸) のうち、24 候補がカバーしないセル:

#### 欠落 ①: 「**トレンドフォロー × MA/MACD/Channel × ML 適応**」が薄い
- 純粋なトレンドフォロー (Donchian, Turtle, MA crossover 系) が **#22 (Adaptive ATR Breakout) のみ**で、しかも「亡き者の改修」というネガティブ前提
- ブレイクアウトはあるが、**「中期トレンド乗っ取り (例: 200日 MA + ADX +動的 trail stop)」** 系統が完全に欠落
- 文献的に **Andreas Clenow "Following the Trend" (2013)** 系の long-term trend following は FX で実装可能

**補強提案 (1 件)**:
- **新規プロポーザル: 「長期トレンドフォロー with ATR Trailing Stop (Donchian Channel + ADX フィルタ + Chandelier Exit)」**
  - エッジ源: Andreas Clenow / Turtle 系 / Saxo Bank Carmot Capital 系の長期実証
  - 通貨/TF: 主要ペア D1 or H4
  - 自己改善: ATR period + Channel period の月次ベイズ最適化
  - 想定 PF: 1.2-1.5 (キャリートレード代替の中長期分散源)
  - **Phase 0 で 1 件追加起草を推奨** (Phase 1 BT 工数 +2 日)

#### 欠落 ②: 「**Order Flow 系の本格実装**」
- #17 (Volume Profile) のみ。**Order Book 分析 / Footprint / Delta** は完全欠落
- ただし FX は OTC 構造で Order Book アクセス困難 (CME futures 経由なら可能だが個人投資家には現実的でない)
- **判定: 意図的除外で OK**。MT5 + Python 制約内では深掘り不可能

#### 欠落 ③: 「**夜間・週末ギャップ取引**」
- 週明け窓開き、米国時間引け後の薄商い活用が完全欠落
- ただし FX は 24h なので「夜間」概念が曖昧、週末ギャップは日曜 22:00 UTC 開場の小さな gap のみ
- **判定: 意図的除外で OK**。FX ではエッジが薄い (株式・先物との違い)

#### 欠落 ④: 「**マルチ通貨相関ベース戦略**」
- #12 (Cointegration) はあるが、「USD バスケット偏り検知」「リスクオン/オフ通貨同期スコア」のような multi-currency correlation 戦略はない
- ただし **#16 (Carry Trade) + #12 (Cointegration)** で構造的にカバー
- **判定: 意図的除外で OK** (既存候補で実質的に補完)

---

### C 違反まとめ

| 欠落カテゴリ | 重要度 | アクション |
|---|---|---|
| ① 長期トレンドフォロー (Donchian/Turtle 系) | **高** | **Phase 0 で 1 件追加起草を推奨** |
| ② Order Flow 本格実装 | 低 | 意図的除外 (技術的制約) |
| ③ 夜間/週末戦略 | 低 | 意図的除外 (FX 特性) |
| ④ Multi-currency 相関 | 中 | 既存候補で補完 (#12 + #16) |

**C 違反処理 = 純増 1 候補** (長期トレンドフォロー)

---

## 4. 粒度の不揃い検出

### 階層混在の指摘

24 候補のうち **3 候補が「単一戦略」ではなく「ポートフォリオ層 (戦略の上位)」**:

| 候補 | レイヤー | 何を組み合わせる? | 個別戦略の前提 |
|---|---|---|---|
| #6 memory_seasonal_regime_gate | **メタ-フィルタ層** | ベース戦略 (EUR_USD H1 RSI) × SeasonalDetector | 既存単一戦略 |
| #8 memory_multi_strategy_portfolio | **ポートフォリオ層** | EUR_USD H1 RSI + USD_JPY M15 RSI の 2 戦略 | 個別戦略 #1, #2 通過前提 |
| #19 internal_yz_vol_regime_router | **ルーター層** | HIGH_VOL モメンタム + LOW_VOL 平均回帰 (排他選択) | 既存 BR + 新規 momentum |
| #23 internal_session_split_strategies | **ルーター層** | Tokyo/London/NY 別の 3 戦略割当 | 既存 BR + MTF + Conservative_Breakout |
| #25 internal_dynamic_portfolio_weighting | **ポートフォリオ層 (動的)** | N 戦略の MWUM 動的重み | 個別戦略多数の Phase 2 通過前提 |

これらは「単一戦略候補」と並べて評価すると、**評価軸 (G1-1 エッジ源 等) が噛み合わない**:
- 単一戦略は「**自前のエッジ源**」を主張
- ポートフォリオ層は「**個別戦略の組み合わせ効果**」が主張、自前エッジは「分散投資原理」のみ

### 階層別の分類

#### 単一戦略レイヤー (Phase 1-2 で精査 BT、戦略確定する)
- #1, #2, #3, #4 (+#24), #7, #9, #10, #11, #12, #13, #14, #15, #16, #17, #18, #20 (+#5+#21), #22, (補強案: 長期トレンドフォロー)
- **= 17 候補** (M 違反統合後)

#### メタ-フィルタ層 (Phase 1-2 で個別戦略と同時 BT 可能、独立して評価)
- #6 (Seasonal Regime Gate)
- → ベース戦略があれば走らせられる。**単一戦略レイヤーに残す**。

#### ルーター層 (Phase 2-3 で個別戦略確定後、ルーティング検証)
- #19 (YZ_vol Regime Router), #23 (Session Split Strategies)
- → 個別戦略 (BR, MTF, Momentum) が Phase 2 通過してから着手するのが論理的
- **判定**: **Phase 1 BT は可能だが、本格採用は Phase 3 案件**

#### ポートフォリオ層 (Phase 4 案件)
- #8, #25
- → 個別戦略の Phase 2 通過が前提条件、それ以前は構築不可能
- **判定**: **Phase 4 案件として保留トレーへ**

### 粒度修正提案

| 候補 | 現在のラベル | 修正後の取扱い |
|---|---|---|
| #6 | 単一 (メタフィルタ) | **単一戦略扱いで OK** (ベース戦略単独でも回せる、フィルタ加除を比較するから) |
| #8 | 単一として並んでいた | **Phase 4 保留** (#1, #2 の Phase 2 通過後に着手) |
| #19 | 単一として並んでいた | **Phase 2-3** (HIGH_VOL モメンタム部分の事前 BT が必要) |
| #23 | 単一として並んでいた | **Phase 2-3** (個別戦略の通過後にセッション割当を最適化) |
| #25 | 単一として並んでいた | **Phase 4 保留** (個別戦略多数の通過前提) |

**粒度処理 = Phase 4 保留 2 件 (#8, #25)、Phase 2-3 候補マーク 2 件 (#19, #23) はラベル変更のみで査読対象継続**

---

## 5. MECE 改善後の候補リスト

### 改善前: 24 候補

### 改善後: 19 候補 (Phase 1-3 査読対象) + 2 候補 (Phase 4 保留)

#### Phase 1-2 単一戦略レイヤー (16 候補)

| # (新) | 旧# | 短縮名 | 戦略タイプ | TF |
|---|---|---|---|---|
| A | 1 | eur_usd_h1_rsi_pullback | MR | H1 |
| B | 2 | usd_jpy_m15_rsi_pullback | MR | M15 |
| C | 3 | mfi_adx_breakout (6ペア) | BO | H1 |
| D | 4+24 統合 | deceased_reversal | MR(反転) | M15/H1 |
| E | 6 | seasonal_regime_gate (フィルタ) | MR + REG | H1+M15 |
| F | 7 | gbp_jpy_m15_high_pf_caution | MR | M15 |
| G | 9 | xgboost_walk_forward | ML | H1 |
| H | 10 | hmm_regime_ensemble | ML+REG | D1 |
| I | 11 | ppo_rl_auxiliary | ML(RL) | H1 |
| J | 12 | cointegration_pairs | STAT | H1 |
| K | 13 | news_sentiment_garch | EVENT | H1 |
| L | 14 | london_breakout_adaptive | BO | H1 |
| M | 15 | meta_labeling_ensemble | ML(フィルタ) | H1/H4 |
| N | 16 | carry_trade_systematic | CARRY | D1 |
| O | 17 | volume_profile_microstructure | MR(VOLM) | M5+H1 |
| P | 18 | eurusd_meanrev_focus | MR | M15 |
| Q | 20+21 統合 | confluence_gate_filter (Bear severity 含む) | MR/TR + ゲート | M15 |
| R | 22 | adaptive_atr_breakout | BO | M15 |
| **S** (補強) | (新規) | **long_term_trend_following_donchian** | **TR** | **D1/H4** |

#### Phase 2-3 ルーター層 (2 候補、Phase 1 BT 可能)
| # | 旧# | 短縮名 |
|---|---|---|
| T | 19 | yz_vol_regime_router |
| U | 23 | session_split_strategies |

#### Phase 3 オプション (LLM 系、ペーパー実測必要)
| # | 旧# | 短縮名 |
|---|---|---|
| (V) | 5 | llm_filter_dual_validation |

#### Phase 4 保留 (ポートフォリオ層、個別戦略確定後)
| # | 旧# | 短縮名 |
|---|---|---|
| - | 8 | multi_strategy_portfolio |
| - | 25 | dynamic_portfolio_weighting |

**改善後の合計**: Phase 1-2 = 19 候補 (P→D 統合で -1、Q→3統合で -2、補強 +1) + ルーター 2 + LLM オプション 1 + Phase 4 保留 2 = **24 → 24 (見かけ同数)** だが**評価レイヤーが分離**。

→ **実質的な査読対象 (Phase 1-2 査読) は 19 候補 + ルーター 2 = 21 候補**

---

## 6. 次フェーズ (6 評価委員査読) で扱うべき候補数の推奨

### 推奨A: **18-21 候補に絞って査読** (MECE 改善実施)

#### A-1: **保守的提案 (推奨)**: 19 候補で査読
- 単一戦略 16 + ルーター 2 + LLM オプション 1 = 19
- **Phase 4 保留 2 件 (#8, #25) は査読対象外**
- 補強案 (S = 長期トレンドフォロー) は Phase 0 で 1 件起草してから

#### A-2: **積極的提案**: 18 候補で査読 (補強案を Phase 0 で起草しない場合)
- 単一戦略 15 (補強案なし) + ルーター 2 + LLM オプション 1 = 18

### 推奨B: **24 候補全部で査読** (MECE タグ付きで)

「**24 候補のまま全部 6 委員で査読し、本監査の M/C 違反タグを各候補のヘッダに付記**」

#### この選択肢が合理的な理由
1. **6 評価委員 × 24 候補 = 144 レビュー** で工数的に十分こなせる (1 委員 = 24 候補、1 候補 30 分なら 12 時間。並列で 2 時間)
2. **「実質同じ」と判定したペアでも、自己改善メカニズムの細部差・撤退条件・実装複雑度に差**があり、6 委員が異なる視点でその差を再評価する余地がある
3. **MECE 統合判断は構造視点だが、6 委員 (karen/ultrathink/pragmatist/Bull/Bear/Tester) は異なる視点を持つ** → 統合判定そのものが委員の議論対象になりうる
4. 反論屋 ULTRA バグ E (「同じデータの別角度の擬似独立」) を本監査が再演する可能性 (= 「実質同じ」と判定したが、6 委員視点では別物だった、というケース)
5. **粒度の不揃い (ポートフォリオ層) も、6 委員が「これは Phase 4 案件として保留すべき」と独立に判断**してくれる方が記録に残る

#### 不採用に値する反論
- 144 レビューは時間効率が悪い → 統合した方が深い議論ができる
- ポートフォリオ層を単一戦略と並列評価すると「ポートフォリオ層が高得点」になりがちで、評価が歪む可能性

### **本監査の最終推奨**: **A-1 + B のハイブリッド**

具体的には:

1. **6 委員には 24 候補全件のレビューを依頼**する (= B 案準拠)
2. ただし、**本監査の M/C 違反タグを各候補ファイルのヘッダに付記** する:
   - `<!-- MECE_AUDIT: M-violation pair = #20 (Confluence Gate), #21 (Bull/Bear Dialectic) -->` のようなコメント
   - `<!-- MECE_AUDIT: Phase-layer = "ポートフォリオ層 (Phase 4 案件)" -->` のようなマーカー
3. **6 委員には「これらのタグを参考にしつつ、独自視点で M/C 違反の妥当性を再評価」と指示**
4. **査読集計フェーズで、Phase 2 進出推奨候補を最終 6-10 件に絞る**ときに、本監査の統合提案を再採用するか判断
5. **Phase 0 で長期トレンドフォロー (補強案 S) を 1 件追加起草**するかは、6 委員レビュー後に決定 (現時点では「保留」)

→ **6 委員に投げる候補数 = 24 件 (タグ付き)**、**Phase 2 進出推奨は 6-10 件に絞る**

---

## 7. 補足: 反論屋教訓の継承度チェック (H 軸)

各候補が `feedback-deceased-world-data-inheritance` / placeholder 禁止 / GBP_JPY 撤退論証をどう扱っているか:

| 候補 | 亡き者DB参照 | placeholder 回避 | GBP_JPY 採用論証 |
|---|---|---|---|
| #1 EUR_USD H1 RSI | ✅ 唯一プラス根拠で活用 | ✅ 既存BT実証 | n/a (採用せず) |
| #2 USD_JPY M15 RSI | ✅ H1で負け→M15 で差別化 | ✅ 既存BT実証 | n/a |
| #3 MFI+ADX Breakout | ⚠️ F15 ADX 経験参照のみ | ⚠️ 6ペアで未BT | 採用 (6ペア中) |
| #4 Deceased Reversal | ✅ 直接活用 | ⚠️ 11日 実取引→未OOS | 反転対象に含む |
| #5 LLM Filter | ✅ ベース選定でEUR_USD採用 | ⚠️ LLM部はBT不能 | n/a |
| #6 Seasonal Gate | ✅ SPEC v2 撤退教訓継承 | ✅ 既存BT (TR) | n/a |
| #7 GBP_JPY M15 | ⚠️ 自己却下 (反論屋ULTRA バグ B再演) | ⚠️ OOS 4件 | **採用論証不十分**と自認 |
| #8 Portfolio (2戦略) | ✅ EUR_USD唯一プラス活用 | ✅ #1+#2 個別BT実証 | n/a |
| #9 XGBoost WFO | ⚠️ Quantinsti EUR/USD赤字事例認知 | ⚠️ 自前BT未実施 | n/a |
| #10 HMM Regime | ⚠️ 亡き者 GBP_JPY 短期保有との不整合認知 | ⚠️ 自前BT未実施 | n/a |
| #11 PPO RL | ⚠️ 全く新系統 | ⚠️ Buy&Hold 収束警告 | n/a |
| #12 Cointegration | ✅ 亡き者単一ペア戦略の失敗を別系統で克服 | ✅ 文献PF 1.3-2.0 | n/a |
| #13 News Sentiment | ⚠️ 全く新系統 | ⚠️ FX BT 未実証 | n/a |
| #14 London Breakout | ⚠️ 亡き者と別系統 (整合確認不可) | ⚠️ 自前BT未実施 | n/a |
| #15 Meta-Labeling | ✅ 亡き者 MTFPullback を Primary 活用 | ✅ Hudson&Thames 文献PF | n/a |
| #16 Carry Trade | ⚠️ 別系統 | ⚠️ 自前FX BT 未実施 | n/a |
| #17 Volume Profile | ⚠️ 別系統 | ⚠️ Tick Volume妥当性未検証 | n/a |
| #18 EUR_USD MR Focus | ✅ EUR_USD唯一プラス活用 | ✅ 既存BT 1.24 | n/a |
| #19 YZ_vol Router | ✅ SPEC v2撤退教訓継承 | ⚠️ HIGH_VOL モメンタム部未BT | n/a |
| #20 Confluence Gate | ✅ 亡き者ConvictionScorer未活用問題を直接修正 | ⚠️ ゲート効果未BT | n/a |
| #21 Bull/Bear Dialectic | ✅ 亡き者ai_reasons NULL 問題直接修正 | ⚠️ ゲート効果未BT | n/a |
| #22 Adaptive ATR BO | ⚠️ 亡き者改修 (警告該当) | ⚠️ 改修効果未BT | n/a |
| #23 Session Split | ✅ 亡き者保有時間問題直接修正 | ⚠️ セッション BT 未実施 | n/a |
| #24 Loser Reverse | ⚠️ Cherry-pick 批判承知 | ⚠️ サンプル過少 | 反転対象 (限定) |
| #25 Dynamic Portfolio | ✅ 亡き者単一失敗モード構造修正 | ⚠️ 個別戦略前提 | n/a |

**観察**:
- **亡き者DB 直接活用**: 12 候補 (✅)
- **既存BT で実証済**: 6 候補 (#1, #2, #6, #8, #12, #18, #15 一部)
- **未BT/未検証** (Phase 1 BT 必須): 18 候補 (⚠️)
- **placeholder 警告該当**: #22 (亡き者改修), #11 (Buy&Hold 罠), #24 (cherry-pick)

→ Phase 1 BT で **「PF > 0.95 を超える事前根拠が薄い 18 候補」を厳しめにスクリーニング** することが重要。本監査の補強案 (S = 長期トレンドフォロー) もこの 18 に含まれる。

---

## 8. 最終結論

### 推奨アクション (優先度順)

1. **24 候補全件を 6 評価委員で査読依頼**する。各候補ファイルに本監査の **MECE タグをコメント付記**する (M-violation / Phase-layer / inheritance-status)
2. **6 委員の集計フェーズで、Phase 2 進出推奨を 6-10 件に絞る** 際、本監査の統合提案 (#5/#20/#21 → #20, #4/#24 → #4) を**再採用するか判断**
3. **Phase 4 保留候補 2 件 (#8 multi_strategy_portfolio, #25 dynamic_portfolio_weighting)** には Phase-layer タグを明示し、評価委員に「Phase 4 案件」として認識させる
4. **補強案 (長期トレンドフォロー Donchian/Turtle 系)** は 6 委員レビュー後に追加起草を判断 (Phase 0 で起草するか、Phase 1 で BT 候補に追加するか)
5. **GBP_JPY M15 (#7)** は自己却下に近い採点 (51) で、6 委員レビューで正式却下を確認。撤退済通貨の再採用論証として参考価値あり

### 6 評価委員の役割分担 (提案)

| 委員 | 主観点 | 重点候補 |
|---|---|---|
| **karen** | placeholder 警告・撤退条件不備 | #11, #22, #24, #7 |
| **ultrathink** | 構造論争 (三重定義罠の再演リスク) | #6, #19, #20 |
| **pragmatist** | スプレッド/スリッページ耐性 | #13, #11, #22, #14 |
| **Bull researcher (新規)** | 上振れシナリオの理論的最大値 | #15, #12, #1, #14 |
| **Bear researcher (既存)** | 下振れシナリオ | #11, #7, #13, #22, #24 |
| **Tester (新規)** | OOS サンプル数・統計的有意性 | #7 (4件), #11 (シード依存), #24 (7件), #2 (11-15件) |

---

## 9. 監査自己評価

### 本監査の制約・限界

1. **構造視点での判定**は厳密だが、6 委員の異視点を完全には予測できない (B 案を推奨理由)
2. **補強案 (長期トレンドフォロー)** の必要性判定は監査者の主観が入る (=「平均回帰 10/24 が多すぎる」という判断)
3. **Phase 4 案件への分離**は粒度判断であり、ユーザーが「ポートフォリオ層も並列査読したい」と希望すれば差し戻し可
4. **45 分制限内**で 24 候補精読の深さは限定的。1 候補あたり 2 分弱でマトリックス化 → 重要な細部 (例: #15 の Triple-Barrier 設定の妥当性) を見落とした可能性

### 確信度マトリックス

| 結論 | 確信度 | 根拠 |
|---|---|---|
| M 違反組① (#5+#20+#21 統合) | **高** | 構造が完全に同型 |
| M 違反組② (#4+#24 統合) | **高** | エッジ源・対象ペアが同じ |
| M 違反組⑥ (#8+#25 ポートフォリオ層) | **高** | 階層が明らかに異なる |
| C 違反 ① (長期トレンドフォロー欠落) | 中 | 主観的判断、6 委員で再評価推奨 |
| 6 委員に 24 件全件投げる推奨 | 中-高 | 反論屋ULTRA バグ E 回避が動機 |

---

**監査終了。**
