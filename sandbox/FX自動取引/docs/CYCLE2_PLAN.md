# 第2サイクル計画書 — signal_v2 + LLM 補完

**作成日**: 2026-05-26
**根拠**: Phase 2 第1サイクル 5/5 FAIL (`docs/proposals/REVIEW_PHASE2.md`)
**目的**: signal_v2 (PF 0.95) を「単独で勝てる戦略を新規構築する」のではなく、「**リアルタイム弱みを LLM で補完して PF を改善する**」アプローチを検証

---

## なぜこの方向か — 第1サイクル 5/5 FAIL の構造的事実

第1サイクル (案B 5候補) はすべて FAIL。その失敗パターンを集約:

| 失敗パターン | 第1サイクル実例 | 第2サイクルでの回避策 |
|---|---|---|
| 統計的妥当性 ≠ 経済的妥当性 | #12 cointegration p<0.05 維持率最高ペアが最大損失源 | **PF 差分のみ測定**、統計指標は補助 |
| ML が数値特徴量から新情報を引き出せない | #15 Meta-Labeling RF AUC<0.5 | **LLM で非数値情報** (ニュース、コンテキスト) を加える |
| Phase 0 BT グリッド偽陽性 | #1, #2 で 60日 yfinance n=11 サンプル偽陽性 | **既知の signal_v2 (PF 0.95) をベース**、新規 BT グリッド不要 |
| self-improvement のシグナル抑制罠 | #1 で 96.4% シグナル抑制で見かけ PF 上昇 | **LLM REJECT 率を必ず可視化**、抑制トレードも別途記録 |
| 負の期待値戦略は分散源にならない | #12 cointegration が分散源失敗 | **PF 0.95 単独で分散源にしない**、補強対象として扱う |
| 自己採点と実 BT の予測力ギャップ | 全候補で self-rating 83 → 実 BT 0.83 | **採点を採用しない**、PF 差分を絶対基準 |

---

## 戦略仕様

### ベース戦略 (確定): signal_v2

`src/spec_v2/signal_v2.py` の ATR breakout (既存実装):
- M15 N=20 高値ブレイクで long、安値ブレイクで short
- SL = ATR(14) × 1.5、TP = ATR(14) × 3.0、RR = 2.0
- 過去 2年実 BT で **PF 0.95 / Sharpe -0.39** (Pragmatist の `_contrarian_bt.py`)

これは **「ぎりぎり負けている」エッジ近傍** = 補強の余地が最も大きい候補。

### 補完層 (検証対象): LLM Direct Filter

各 signal_v2 シグナル時点で:
1. **市況情報を取得** (前後 24h の関連通貨価格、当日の経済指標カレンダー、ニュース要約 [任意])
2. LLM (Claude Sonnet 4) に判定させる:
   - **CONFIRM**: 取引推奨 (signal_v2 と一致)
   - **CONTRADICT**: 反対方向を取るべき (signal_v2 と逆方向)
   - **NEUTRAL**: 取ってよい (積極推奨ではない)
   - **REJECT**: 取らない (危険な状況)
3. CONFIRM / NEUTRAL のみ実取引対象、CONTRADICT / REJECT は除外

これは:
- yo_hide 流 LLM フィルタ (memory `research_ai_trading_2026_03.md`)
- 亡き者 AIAdvisor 枠組みの蘇生 (内部 phase0 が発見: 本番で `ai_decision = NULL` だった)

### LLM プロンプト雛形 (Phase 0' で確定)

```
あなたは FX 自動取引のリスク判定エージェントです。
以下の信号について、取るべきか判定してください。

[シグナル情報]
- ペア: {pair}
- 時刻: {timestamp_utc}
- 方向: {long/short}
- エントリー: {entry_price}
- SL: {sl_price} ({sl_pips} pips)
- TP: {tp_price} ({tp_pips} pips)

[市況コンテキスト]
- 関連通貨直近24h: {related_moves}
- 当日経済指標: {econ_calendar}
- 市況メモ: {market_context}  ← 任意 (ニュース要約)

[判定]
以下のいずれかを返答してください:
- CONFIRM: シグナルを取るべき (強い同意)
- NEUTRAL: 取ってよい (積極推奨ではない)
- CONTRADICT: 反対方向を取るべき
- REJECT: 取らない (危険な状況)

理由を1-2文で述べてください。
```

---

## 検証法 — 過去5年シグナルへの遡及適用

### Step 1: 過去シグナル抽出 (analyst H2)
- 過去5年 GBP_JPY, USD_JPY, EUR_USD の M15 OHLC
- signal_v2 ロジックを走らせて **全シグナル抽出**
- 各シグナルに以下のメタデータを付与:
  - pair, timestamp_utc, direction, entry, SL, TP, ATR
  - 24h 後の実際の高値・安値・終値 (BT 用)
  - 関連通貨直近24h 動き
  - 当日経済指標フラグ (主要発表があったか)

出力: `data/signal_v2_historical_signals.csv` (例 1000+ 件)

### Step 2: LLM フィルタ適用 (general-purpose H4)
- 上記 CSV を読んで各行を LLM Claude Sonnet 4 に判定させる
- 結果を `data/llm_filter_decisions.csv` に保存:
  - signal_id, llm_decision, llm_reasoning, api_cost
- **コスト見積もり**: 1000件 × ~1円/コール (Sonnet 4) = **約1,000円**

### Step 3: PF 差分集計 (H5)
- signal_v2 単独 PF (全シグナル)
- LLM CONFIRM のみ PF
- LLM CONFIRM + NEUTRAL のみ PF (REJECT/CONTRADICT 除外)
- ペア別、TF別の集計

各集計に対し:
- Trade 件数
- 勝率、平均勝ち pips、平均負け pips
- PF, Sharpe, MaxDD
- スプレッド込みの PnL

---

## ゲート判定 (Phase 2' 進出可否)

### 必須条件
- **PF 差分 ≥ +0.3 ポイント**: signal_v2 単独 0.95 → LLM フィルタ後 **PF ≥ 1.25** で価値あり
- **OOS trades ≥ 30**: フィルタ後の残存件数が統計的に意味ある規模
- **LLM コスト持続可能**: 月間運用コスト見積もり ≤ 月5,000円 (個人運用許容範囲)

### 望ましい (加点)
- **PF ≥ 1.5** (機会費用 米国債4% を超える経済性)
- **Sharpe ≥ 0.8** (リスク調整後リターン健全)
- **LLM 判断の説明可能性**: REJECT 理由のパターン分析で「危険な状況」が学習可能

### 即時棚上げ (FAIL)
- PF 差分 < +0.1 (微改善のみ)
- LLM REJECT 率 > 80% (フィルタきつすぎ、サンプル不足)
- LLM 判断が一貫性なし (同じ状況で異なる判定)

---

## 検証結果 → 次のアクション

| 結果 | 次のステップ |
|---|---|
| **PF +0.3 以上 改善** | Phase 0' で LLM 系候補4-5本展開 → 各候補で同様検証 → Phase 2' 進出 |
| **PF +0.1〜+0.3 改善** | プロンプト調整・市況コンテキスト拡充で再検証 (追加 1,000円) |
| **PF 改善なし or 悪化** | 選択肢 B/C/D へ (新軸 / 撤退 / 半自動アシスト) |

---

## リスク・既知の弱点

1. **LLM 判断の過去再現性**: BT 結果を異なるセッションで再現できない可能性 (LLM 応答の非決定性)
   - 対策: `temperature=0`、複数回実行で安定性確認
2. **市況コンテキストの後付けバイアス**: 過去ニュース要約は「事後的知識」を含む可能性
   - 対策: ニュース要約は使わず、時系列で利用可能だった情報 (経済指標カレンダー、関連通貨価格) のみ
3. **LLM API コスト持続性**: 本番運用で月数千円〜
   - 対策: Sonnet 4 → Haiku 4.5 へ降格可能か、フィルタ判定の精度比較
4. **既存 AIAdvisor との重複**: 亡き者の AIAdvisor 枠組みが本番で NULL だった原因究明
   - 対策: 本検証で新規実装、亡き者コードは参考のみ

---

## 撤退条件 (事前明文化)

- Phase 0' 候補3本起草後、いずれも PF 差分 +0.3 未達なら **第2サイクル全体を撤退**
- LLM コスト月10,000円超なら撤退
- 半年検証 (デモ) で PF<1.0 維持なら撤退

---

## 関連
- Phase 2 第1サイクル結果: `docs/proposals/REVIEW_PHASE2.md` (作成予定)
- 撤退記録: `docs/RETREAT_2026-05-26.md`
- 採点フレーム: `docs/PROPOSAL_TEMPLATE.md`
- BT 参考実装: `scripts/_contrarian_bt.py` (signal_v2 PF 0.95 算出元)
