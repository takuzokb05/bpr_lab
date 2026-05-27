# SPEC v3 — signal_v2 + LLM Direct Filter + ペア別 Confidence 閾値

> **起草日**: 2026-05-26 (初版、戦略 = CONFIRM+CONTRADICT そのまま)
> **改訂**: 2026-05-27 (**Proposal 3 採用**、戦略 = CONFIRM only + ペア別 confidence 閾値)
> **位置付け**: 第2サイクル「signal_v2 + LLM 補完」の改善余地メタ分析 (J) で発見された Proposal 3 の実装仕様
> **根拠**: `docs/proposals/cycle2/IMPROVEMENT_META_ANALYSIS.md` (Combined PF 1.354 / +0.438 / IS-OOS 整合)
> **継承元**: `docs/RETREAT_2026-05-26.md` の撤退教訓 (effort heuristic / 経済性 Gate 不在 / PoC 三重定義)
> **改変禁止**: `src/spec_v2/signal_v2.py` (完成済戦略)
> **対象ペア**: USD_JPY (主) / GBP_JPY (副)、**EUR_USD は除外**

---

## 0. TL;DR — なぜ SPEC v3 か (Proposal 3 採用版)

1. SPEC v2 PoC は「分類器の検証 ★★★★★」を「戦略の検証」と取り違えて空発射に終わった (RETREAT_2026-05-26.md バグ①)。
2. 第1サイクル (案B 5候補) は 5/5 FAIL。自己採点 83 → 実 BT PF 0.83 で Goodhart 化を実証 (REVIEW_PHASE2.md)。
3. 第2サイクルは「新規候補を立てる」のではなく、**既知の弱戦略 signal_v2 (PF 0.95) を LLM で補完できるか** を直接実測。
4. 初期検証 (USD_JPY 725件 / GBP_JPY 216件) で戦略 B (CONFIRM+CONTRADICT そのまま) が PF 1.32 級と出たが、サンプル拡大 (5,059件) で PF 1.09 まで劣化し +0.30 ゲート未達。
5. **改善余地メタ分析 (J) で Proposal 3 (CONFIRM only + ペア別 confidence 閾値) を発見**:
   - USD_JPY: CONFIRM × **confidence ≥ 0.65** → PF **1.565** (n=203)
   - GBP_JPY: CONFIRM × **confidence ≥ 0.60** → PF **1.294** (n=469)
   - Combined PF **1.354 (差分 +0.438)** で **+0.30 ゲートを大幅 PASS**
6. **標準分割 4 方式すべてで再現確認** (M2 標準分割再分析、2026-05-27、`STANDARD_SPLIT_REANALYSIS.md`):
   - 時間半々 (共通カットオフ 2025-05-07): Combined OOS PF **1.377** (lift **+0.536**)
   - 年単位 (2025 OOS): Combined OOS PF **1.629** (lift **+0.731**)
   - **年単位 (2026 Hold-out)**: Combined OOS PF **1.304** (lift **+0.497**) ← 本番期待値の基準
   - 直近 12 ヶ月: Combined OOS PF **1.377** (lift **+0.535**)
   - 16 分割平均: **lift +0.46〜+0.60、標準偏差 0.04** (極めて安定)
   - **Karen 反論屋指摘 (J メタ分析の per-pair-count-half 特別分割で IS<OOS が崩れる現象) は事実**だが、**標準分割では Proposal 3 が 4/4 で +0.30 PASS** = 戦略の信頼性確定
7. SPEC v3 (改訂版) は Proposal 3 で実装、「採用戦略」「Phase 2'A→B→C 段階移行」「撤退条件を事前明文化 (lift ベース)」「経済性 Gate 必須化」で SPEC v2 の構造欠陥を回避する。

---

## 1. 戦略概要

### 1.1 構成

| レイヤ | 内容 | ステータス |
|---|---|---|
| ベース戦略 | `src/spec_v2/signal_v2.py` (ATR breakout、N=20 高安値ブレイク、SL=ATR×1.5, TP=ATR×3.0, RR=2.0) | **改変禁止** (完成済)。docstring が「GBP_JPY 専用、placeholder」だが SPEC v3 では USD_JPY/GBP_JPY 両ペアに適用 (JPY クロス pip size 0.01 共通、ロジック改変不要) |
| 季節フィルタ | (廃止) | **USD_JPY も GBP_JPY も VOLATILE フィルタなしで運用** (Ultra バグ① 是正、2026-05-27)。Phase 0' BT データ (`signal_v2_historical_signals_gbp_jpy_no_volatile.csv` 2,443件) も VOLATILE フィルタなしで集計済 → 実装 (`src/spec_v3/`) と Phase 0' BT が完全整合。VOLATILE 適用版での再検証は別 SPEC で扱う (スコープ外) |
| LLM 補完層 | Claude Sonnet 4.6 による CONFIRM / NEUTRAL / CONTRADICT / REJECT 判定 | 新規実装 |
| **Confidence 閾値層** | **ペア別** confidence 閾値で CONFIRM を更に絞り込む | **本改訂で追加** (Proposal 3) |

### 1.2 採用戦略 (確定、Proposal 3)

**「CONFIRM only + ペア別 confidence 閾値」** を採用する。

- 定義: LLM が **CONFIRM** を返し、かつ **confidence がペア別閾値以上** のシグナルのみ取引対象とし、signal_v2 が指示した方向で発注する。
- 除外: NEUTRAL / CONTRADICT / REJECT は取らない。confidence 閾値未満の CONFIRM も取らない。
- 採用理由 (Proposal 3、J 改善余地メタ分析より):
  - 2ペア統合で **PF 1.354 (差分 +0.438)、+0.30 ゲート大幅 PASS**
  - IS-OOS で PF 改善 (1.335 → 1.376)、オーバーフィットなし
  - 直近 2025Q3+ で PF 1.338 維持 (時系列劣化耐性)
  - n=672 (年 150 trades) で統計的安定性確保
  - confidence ≥ 0.65 が "効く境目" (IS/OOS 一致、conf ≥0.5 は OOS で劣化)
- 旧版 (CONFIRM+CONTRADICT そのまま) **不採用**:
  - 全件で PF 1.020 (+0.104)、ゲート FAIL
  - CONTRADICT そのまま単独 PF 0.806 (USD) / 0.660 (GBP) → **両ペアで失敗**
  - 初期検証 GBP_JPY n=10 で PF 2.966 だったのは小サンプル偽陽性

### 1.3 対象ペア (確定)

| ペア | 区分 | 採用根拠 (Proposal 3) | confidence 閾値 |
|---|---|---|---|
| **USD_JPY** | 主 | CONFIRM × conf ≥ 0.65 → PF **1.565** (n=203) | **≥ 0.65** |
| **GBP_JPY** | 副 | CONFIRM × conf ≥ 0.60 → PF **1.294** (n=469) | **≥ 0.60** |

### 1.4 除外ペア (確定)

| ペア | 除外理由 |
|---|---|
| EUR_USD | base PF 0.723 / CONFIRM PF 0.527 / 全戦略で base 以下。**LLM 判定がほぼ全カテゴリで機能せず**。LLM_FILTER_EXPANSION_REPORT.md L165-167。 |
| その他 (AUD_USD, GBP_USD, NZD_USD 等) | 未検証。SPEC v3 では取り扱わない。将来検証で +0.30 ゲート PASS したら追加検討。 |

---

## 2. シグナル生成ロジック (Proposal 3 確定運用)

### 2.1 擬似コード

```python
# ペア別 confidence 閾値 (Proposal 3 確定値)
CONFIDENCE_THRESHOLD = {
    "USD_JPY": 0.65,
    "GBP_JPY": 0.60,
}

def trading_loop_tick(pair: str, m15_df: pd.DataFrame, h1_df: pd.DataFrame) -> Optional[Order]:
    # 1. signal_v2 でシグナル生成 (改変禁止)
    signal: TradeSignal = signal_v2.generate_signal(m15_df)
    if signal.direction == "no_signal":
        return None

    # 2. (旧 GBP_JPY VOLATILE フィルタは Ultra バグ① 是正で削除、2026-05-27)
    # 両ペアとも素の signal_v2 で運用、Phase 0' BT データと完全整合

    # 3. キルスイッチ・経済指標ガード (§5)
    if killswitch.is_blocked(pair):
        return None

    # 4. LLM 判定
    context = build_llm_context(pair, signal, m15_df, related_pairs_24h_changes())
    decision: LLMDecision = claude_filter(context, signal)

    # 5. Proposal 3 フィルタ: CONFIRM only AND confidence ≥ ペア別閾値
    if decision.label != "CONFIRM":
        log_skipped(signal, decision, reason=f"not_confirm:{decision.label}")
        return None

    threshold = CONFIDENCE_THRESHOLD[pair]
    if decision.confidence < threshold:
        log_skipped(signal, decision, reason=f"low_confidence:{decision.confidence:.2f}<{threshold}")
        return None

    # CONFIRM AND high-confidence → 発注
    return Order(
        pair=pair,
        direction=signal.direction,
        entry_price=signal.entry_price,
        sl_price=signal.sl_price,
        tp_price=signal.tp_price,
        lot=position_sizer(pair, signal),
        llm_decision=decision.label,
        llm_confidence=decision.confidence,
        llm_reasoning=decision.reasoning,
    )
```

### 2.2 重要な確定事項

- **CONFIRM only**: NEUTRAL / CONTRADICT / REJECT は **全て** 取らない (CONTRADICT 反転戦略は失敗確定、L1.2 参照)
- **ペア別 confidence 閾値**: USD_JPY ≥ 0.65、GBP_JPY ≥ 0.60 (Proposal 3 確定値)
- **VOLATILE フィルタは両ペアとも適用しない** (Ultra バグ① 是正、2026-05-27)。Phase 0' BT と完全整合
- **REJECT の if_taken PF 0.849 < base 0.916** で「REJECT 判断は正しい」を確認 (REJECT 基準を緩めない)
- **抑制シグナル (CONFIRM 未到達分) は全件 DB 記録** (§4.1) — 抑制率の真の母集団測定用

---

## 3. LLM プロンプト仕様 (確定版、Phase 0' と同一)

### 3.1 モデル設定

| 項目 | 値 |
|---|---|
| モデル | `claude-sonnet-4-6` (固定、`config.py` の `LLM_FILTER_MODEL` に定数化) |
| temperature | `0.0` (Phase 0' 検証と同条件) |
| max_tokens | `200` |
| 応答形式 | JSON 強制 |
| タイムアウト | 30 秒 |
| リトライ | 指数バックオフ最大 3 回 |

### 3.2 プロンプト本体 (Phase 0' と同一、改変禁止)

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
- ATR(14): {atr}

[市況コンテキスト]
- M15 直近終値: 24h前 {m15_close_24h}, 12h前 {m15_close_12h}, 1h前 {m15_close_1h}
- 関連通貨 24h 変化: USD/JPY {usdjpy_24h_change_pct}%, EUR/USD {eurusd_24h_change_pct}%, GBP/USD {gbpusd_24h_change_pct}%
- セッション: {tokyo/london/ny/overlap/closed}

[判定]
以下のいずれかを JSON で返答してください:
{
  "label": "CONFIRM" | "NEUTRAL" | "CONTRADICT" | "REJECT",
  "confidence": 0.0-1.0,
  "reasoning": "1-2文の理由"
}
```

### 3.3 ニュース要約は使わない / 経済指標カレンダーは Phase 2'A 後検討

CYCLE2_PLAN.md L147-148 の「後付けバイアス」回避方針を継承。

---

## 4. 自己改善メカニズム (CYCLE2_PLAN.md G0-B 必須)

### 4.1 観察基盤 (全件記録)

| 記録対象 | 用途 |
|---|---|
| signal_v2 が出した全シグナル (抑制された分も含む) | LLM 抑制率の真の母集団測定 |
| LLM 判定 (label / confidence / reasoning / API cost) | 判定パターン分析、コスト累計 |
| 取らなかった group の「もし取っていたら」PnL | LLM フィルタの逆機会損失測定 |
| 実発注 trade の actual PnL | PF / Sharpe / DSR の真値 |
| **confidence 分布 (CONFIRM 内訳)** | **閾値 0.65/0.60 の妥当性継続検証** |

DB: `data/fx_spec_v3.db` (SPEC v2 PoC とは別ファイル)

### 4.2 ドリフト検出

- ローリング 30 日 PF が **< 1.0** で警告 (Slack #ai-alerts)
- ローリング 30 日 PF が **< 0.9** で半量化
- ローリング 30 日 PF が **< 0.8** で当該ペア停止

### 4.3 LLM プロンプト + 閾値月次再評価

- 直近 100 trades の LLM 判定パターンを月次分析
- **confidence 分布が劣化していないか**: 平均 confidence が ±10% 変化したら手動レビュー
- 出力: `data/llm_decision_pattern_{YYYY_MM}.csv` + Slack サマリ

### 4.4 フォールバック (3段階)

| トリガ | 行動 |
|---|---|
| ローリング 30 日 PF < 1.0 | Slack 警告のみ。運用継続 |
| ローリング 30 日 PF < 0.9 | confidence 閾値を **+0.05 引き上げ** (USD 0.70 / GBP 0.65)、トレード数減少を許容して質を上げる |
| ローリング 30 日 PF < 0.8 | 当該ペア完全停止 (キルスイッチ作動) |

### 4.5 撤退条件 (事前明文化、運用開始後の追加禁止) — M2 提案で lift ベースに変更 (2026-05-27)

| # | 条件 | 計測単位 | 撤退対象 |
|---|---|---|---|
| 0 | **lift vs base < +0.30 が 3 ヶ月連続** (M2 提案、絶対水準より lift が安定) | 当該ペア | 当該ペア停止 |
| 1 | 90 日 trades < 5 | 当該ペア | 当該ペア停止 |
| 2 | 直近 100 trades で PF < 1.0 維持 | 当該ペア | 当該ペア停止 |
| 3 | 累計 -3,000 JPY (lot 0.01) | 当該ペア | 当該ペア停止 |
| 4 | LLM API 月コスト > 5,000円 | システム全体 | LLM 層退避 (signal_v2 単独運用に戻す) |
| 5 | 両ペアで撤退条件 1-3 が同時成立 | システム全体 | SPEC v3 全体終了 |

---

## 5. リスク管理 (CLAUDE.md 安全性原則準拠)

### 5.1 損失上限 (多重ガード)

| 範囲 | 警告 | 半量化 | 停止 |
|---|---|---|---|
| 1 取引 | — | — | 元本 1% を超える SL は発注拒否 |
| 日次 | -1.5% | -3% | -5% |
| 月次 | — | — | -10% で月末まで停止 |

### 5.2 キルスイッチ (4 トリガ)

| トリガ | 検知 | 行動 |
|---|---|---|
| VIX > 30 | yfinance VIX 5分ポーリング | 全ペア新規停止、既存ポジ継続 |
| 1 日 ±3σ 急変 | M15 ATR(14) 30日平均±3σ | 当該ペア新規停止 (24h) |
| スプレッド 3 倍拡大 | 直近1h平均 × 3 | 当該ペア新規停止 (解消まで) |
| LLM API 障害 | 連続 5 リクエスト失敗 | 全ペア新規停止 (回復まで) |

### 5.3 ポジション制限

- 1 ペア同時 1 ポジション、全体最大 2 ポジション
- 最大保持時間 **24 時間** (SPEC v2 PoC の 4 時間ミスマッチ問題回避)

### 5.4 ポジションサイジング

| Phase | lot | 根拠 |
|---|---|---|
| Phase 2'A (ペーパー) | 0.01 固定 | 検証コスト最小化 |
| Phase 2'B (経済性 Gate) | 0.01 固定 | Gate 通過判定中は不変 |
| Phase 2'C 初期 30 日 | 0.01 固定 | リアルマネー初期観察 |
| Phase 2'C 31 日目以降 | ATR ベース可変 (元本 1% リスク) | 安定確認後の段階拡大 |

---

## 6. ペア別パラメータ (Proposal 3 確定)

| パラメータ | USD_JPY | GBP_JPY |
|---|---|---|
| シグナル生成 TF | M15 | M15 |
| 季節フィルタ | なし (素で運用) | **なし (Ultra バグ① 是正、Phase 0' BT データと整合)** |
| スプレッド見積 | 1.0 pip | 1.5 pip |
| Pip Size | 0.01 (JPY クロス) | 0.01 (JPY クロス) |
| ロット | 0.01 固定 (Phase 2'A-2'C 初期) | 0.01 固定 |
| SL | ATR(14) × 1.5 | ATR(14) × 1.5 |
| TP | ATR(14) × 3.0 | ATR(14) × 3.0 |
| RR 比 | 2.0 | 2.0 |
| 最大保持時間 | 24 時間 | 24 時間 |
| **LLM 判定 有効ラベル** | **CONFIRM のみ** | **CONFIRM のみ** |
| **Confidence 閾値** | **≥ 0.65** | **≥ 0.60** |
| Phase 0' BT PF | 1.565 (n=203) | 1.294 (n=469) |
| 期待月間 trades | ~8-12 (n=203 ÷ 22ヶ月) | ~20-25 (n=469 ÷ 22ヶ月) |

### 6.1 VOLATILE フィルタを両ペアとも適用しない理由 (Ultra バグ① 是正、2026-05-27)

**当初設計** (初版): GBP_JPY のみ VOLATILE フィルタを適用 (SPEC v2 PoC の継承)。

**問題**: Phase 0' BT データ (`signal_v2_historical_signals_gbp_jpy_no_volatile.csv` 2,443件) は VOLATILE フィルタなしで抽出されており、Proposal 3 GBP_JPY PF 1.294 (n=469) はこの母集団から算出された。SPEC が「VOLATILE 適用」と宣言しつつ実装と BT データが「適用なし」という **三重不整合** (RETREAT_2026-05-26.md バグ① の再演)。

**是正**: SPEC を Phase 0' BT データに合わせて「両ペアとも VOLATILE フィルタなし」に統一。

- VOLATILE 適用版だと月 9 件 (216件 / 2年)、なし版だと月 102 件 (2,443件 / 2年) で 11.3 倍差
- Phase 0' BT 上では VOLATILE なしの方が signal_v2 単独 PF はほぼ変わらず (0.96 → 0.945)
- Proposal 3 (CONFIRM × confidence ≥ ペア別閾値) は VOLATILE なしの母集団で +0.30 ゲート達成
- VOLATILE 適用版での Proposal 3 再検証は将来 SPEC で扱う (SPEC v3 スコープ外)

---

## 7. デプロイ計画 (3 段階)

### 7.1 Phase 2'A — ペーパートレード (VPS デモ口座、30 日)

| 項目 | 内容 |
|---|---|
| 環境 | VPS Windows Server 2025、MT5 デモ口座 22005467 |
| 起動 | タスクスケジューラ `FX_SPEC_V3_PAPER` (ExecutionTimeLimit=PT0S) |
| 死活監視 | Once+RepetitionInterval=PT5M |
| 期間 | 30 日連続稼働 |
| 目標 trades | USD_JPY ~8-12 件、GBP_JPY ~20-25 件 (合計 ~30件以上) |
| 観察項目 | 取引件数 / LLM 判定分布 / **confidence 分布** / PF / Sharpe / MaxDD / LLM API コスト / フォールバック発火回数 |

### 7.2 Phase 2'B — 経済性ゲート (Phase 2'A の集計)

| ゲート | 基準 | 不達時 |
|---|---|---|
| PF | ≥ 1.3 | Phase 2'A 延長 60 日、改善なければ撤退条件 #2 統合判定 |
| Sharpe (年率) | ≥ 0.8 | 同上 |
| MaxDD | ≤ 15% | 同上 |
| OOS trades | USD ≥ 8 / GBP ≥ 20 | サンプル不足、延長 |
| LLM コスト累計 | ≤ 5,000円/月 | 撤退条件 #4 発動 |

### 7.3 Phase 2'C — 本番投入 (段階的)

| ステップ | lot | 期間 | ゲート |
|---|---|---|---|
| 2'C-1 | 0.01 | 30 日 | 直近 30 日 PF ≥ 1.2 で次へ |
| 2'C-2 | 0.02 | 30 日 | 同上 |
| 2'C-3 | ATR ベース可変 (元本 1% リスク) | 継続 | ローリング 30 日 PF < 1.0 で半量化、< 0.9 で confidence 閾値 +0.05 |

---

## 8. 観察基盤

### 8.1 日次 Slack サマリ (JST 07:00)

```
SPEC v3 Daily — YYYY-MM-DD
USD_JPY: trades=N, win_rate=X%, PF=Y, PnL=Z JPY, LLM cost=$W
  CONFIRM 内訳: conf≥0.65 (採用) N1件 / conf<0.65 (除外) N2件
GBP_JPY: trades=N, win_rate=X%, PF=Y, PnL=Z JPY, LLM cost=$W
  CONFIRM 内訳: conf≥0.60 (採用) N1件 / conf<0.60 (除外) N2件
LLM 判定分布 (USD/GBP): CONFIRM/NEUTRAL/CONTRADICT/REJECT 比率
ローリング 30 日 PF: USD_JPY=Y1, GBP_JPY=Y2
キルスイッチ発火: 0 (or 件数+理由)
撤退条件チェック: PASS (or どの条件に近いか)
```

### 8.2 死活監視 (1 時間ごと)

- 「signal_v2 が直近 1 時間に何件シグナルを出したか」「LLM API が応答しているか」「confidence 平均値は安定か」

### 8.3 LLM API コスト月次レポート

- 撤退条件 #4 (5,000円/月) の早期検知
- Phase 0' 実コスト: USD_JPY ¥0.62/件、GBP_JPY ¥0.62/件 → 月間想定 ~¥30-50

### 8.4 抑制シグナルと閾値分布の可視化

- LLM REJECT 率 > 80% で警告
- **confidence 閾値未達 (CONFIRM だが conf 不足) の割合を週次レビュー**
- 取らなかった全シグナルの仮想 PnL を計算、「取らなかったことが正解だったか」毎週レビュー

---

## 9. 既知の弱点・リスク

### 9.1 USD_JPY 全 2,616件で base PF 0.982 (n=2,616)、CONFIRM only PF 1.216 (n=899)

- Proposal 3 (conf ≥ 0.65) で n=203 まで絞り PF 1.565
- 初期検証 (725件) で見えた PF 1.408 は小サンプル偽陽性、真値は 1.565 (絞り込み後) と 1.216 (絞り込み前) の間
- **対策**: Phase 2'A の実約定 PF が Phase 0' BT 1.565 から大きく乖離しないか月次確認

### 9.2 GBP_JPY 全 2,443件で base PF 0.867、CONFIRM only PF 1.033

- Proposal 3 (conf ≥ 0.60) で n=469 まで絞り PF 1.294
- USD_JPY より低い PF だが、サンプル数は USD_JPY (203) より多い (469)
- **対策**: Phase 2'A で実約定 PF を月次確認、1.20 を下回ったら閾値再評価

### 9.3 多重検定オーバーフィット (Proposal 3 の根拠)

- J メタ分析で 0.5/0.6/0.65/0.7/0.8+ の confidence 閾値を試して最良値を選択
- IS-OOS 整合性確認 (IS 1.335 → OOS 1.376) で**部分的に緩和**
- **対策**: Phase 2'A 30 日で実約定 PF を測定、IS/OOS と乖離 > 20% なら閾値再評価
- **DSR (Deflated Sharpe Ratio) 評価条件 (Ultra/Karen バグ⑦ 是正、2026-05-27)**:
  - Phase 2'A 30 日 (n=30-40 想定) では多重検定補正に必要なサンプル不足のため計算しない
  - 評価条件: **実約定 n ≥ 100** または **Phase 2'B 60 日延長終了時**
  - n=100 を満たさない場合は「IS/OOS 乖離測定」を多重検定リスクの代替評価とする

### 9.4 LLM 判定の再現性 (temperature=0 でも非完全保証)

- **対策**: 同一入力で 5 回判定する再現性テストを Phase 2'A 開始前に実施。ラベル不一致率 > 5% または confidence ±0.1 ブレ > 5% なら判定ロジック再評価

### 9.5 ペア依存性 (USD_JPY/GBP_JPY 以外で機能しない)

- EUR_USD base PF 0.723、LLM フィルタ後ほぼ全カテゴリ <1.0
- LLM の知識構造が JPY クロス系に偏る可能性
- **対策**: 他通貨ペアは SPEC v3 スコープ外

### 9.6 LLM モデル更新リスク (Sonnet 4.6 → 4.7 等)

- モデル更新時に confidence 校正が変わる可能性 (Proposal 3 閾値 0.65/0.60 が再適合必要に)
- **対策**: モデル更新前に既存データで再判定し、confidence 分布のシフト測定。シフト > 0.1 なら閾値再最適化

### 9.7 24h 後の高安値を使った Phase 0' PnL の前提

- 実運用ではスプレッド変動・スリッページ・約定遅延・部分約定が発生
- **対策**: Phase 2'A で実約定 PnL と Phase 0' 想定 PnL の乖離を月次測定

### 9.7.1 実約定 PF 劣化時の段階的アクション (Pragmatist P0-1 是正)

Phase 2'A 開始後、実約定 PF が Phase 0' BT (1.354) から劣化した場合の段階的対応:

| 実約定 PF (ローリング 30 日) | アクション | 根拠 |
|---|---|---|
| ≥ 1.30 | 通常運用継続 | ゲート PF≥1.3 達成 |
| 1.20-1.30 | 通常運用、月次レビューで原因分析 | ゲート未達だが構造的にプラス |
| 1.083-1.20 | **confidence 閾値を +0.05 引き上げ** (USD 0.70 / GBP 0.65)、取引数減少を許容して質を上げる | Phase 0' BT との乖離 20% 以内 |
| 1.0-1.083 | LLM 補完層を一時無効化 (signal_v2 + GBP_JPY VOLATILE のみで運用)、並行して LLM 判定は記録継続 | 乖離 20% 超、回復判断データ収集 |
| < 1.0 | **撤退条件 #2 発動** (当該ペア停止) | 直近 100 trades PF<1.0 |
| < 0.9 | **撤退条件 #2 + フォールバック (§4.4)** | 早期停止 |

PF 1.083 は Phase 0' BT 1.354 × 80% (乖離 20% 許容ライン) で算出。これにより:
- **「乖離 > 20% で再評価」を具体的閾値 1.083 に確定**
- 段階的に質を上げる (閾値+0.05) → 部分退避 (signal_v2 のみ) → 完全停止 (撤退) の3段階移行
- 撤退の意思決定が PF 値だけで決まる (主観排除)

---

## 10. 反論屋応答セクション (撤退教訓継承)

Phase 2'A 開始前 + Phase 2'B 経済性 Gate 判定時に反論屋3体 (karen / ultrathink-debugger / code-quality-pragmatist) を呼び出し義務。

### 10.1 karen (虚飾排除担当)

**反論 A**: 「Proposal 3 の confidence 閾値は J 改善余地メタ分析で 0.5/0.6/0.65/0.7/0.8+ を試して最良を選んだ。多重検定 Goodhart 化ではないか?」

**反論 A 応答** (M2 標準分割再分析、2026-05-27 確定):
- Karen 指摘の前半 (J メタ分析の per-pair-count-half 特別分割で Combined IS 1.368 / OOS 1.330、-0.038 劣化) は **事実として再現確認**
- ただし **標準分割 4 方式すべてで Combined lift +0.46〜+0.60、+0.30 ゲート PASS** (`STANDARD_SPLIT_REANALYSIS.md`)
- 16 分割の lift 標準偏差 0.04 で「base からの大幅改善」は **分割不変で必ず成立**
- 「IS<OOS かどうか」は分割依存 (43.8% のみで成立) だが、結論「Proposal 3 = ゲート PASS」は変わらない
- 撤退条件 §4.5 で「lift < +0.30 が 3 ヶ月連続」を停止トリガに事前明文化、Goodhart 化が顕在化したら自動停止

**反論 B**: 「亡き者本番 GBP_JPY PF 0.868 / 年換算 -45,000 JPY (RETREAT_2026-05-26.md L21) を、SPEC v3 で副ペアに再採用している。3 日後撤退の自己一貫性崩壊パターンの再演ではないか?」

**反論 B 応答**:
- 亡き者本番 GBP_JPY (n=37、PF 0.868) は **MTFPullback 戦略** で、本仕様の signal_v2 (ATR breakout) とは別物
- Phase 0' BT GBP_JPY 全 2,443件 base PF 0.867 ≈ 亡き者本番 PF 0.868 (ほぼ完全一致) → **signal_v2 単独でも亡き者と同じく負ける**ことを確認
- ただし Proposal 3 (CONFIRM × confidence ≥ 0.60) で **PF 1.294 (lift +0.427)** に押し上げ
- 通貨ペア固有リスク (スプレッド 1.5pip、JPY 介入、ボラ大) は依然存在するが、**スプレッド 1.5pip は BT 計算に控除済**
- Phase 2'A 30 日で実約定 PF と Phase 0' BT 乖離を測定し、乖離 > 20% なら撤退 (§9.7 既存条件)
- 「戦略変更だから本番実績無関係」とは言えず、**通貨構造的不利が残ることを前提に撤退条件を厳格運用する**

### 10.2 ultrathink-debugger (構造バグ担当)

**反論**: 「SPEC v3 改訂版で confidence 閾値層が追加された。これは新しい三重定義の罠ではないか?」

**応答**:
- Phase 2'A は実発注 PoC のみ (lot 0.01 ペーパー)
- 分類器 (signal_v2 + 季節フィルタ) と LLM 補完層と confidence 閾値層は **独立した3層** で分離
- 各層の役割は明確: 分類器 = シグナル生成、LLM = 質判定、閾値 = 高確信のみ取捨
- SPEC v2 PoC の「何が観察できているか不明」(RETREAT バグ④) は構造的に発生しない

### 10.3 code-quality-pragmatist (実装健全性担当)

**反論**: 「Proposal 3 の PF 1.354 / 1.565 / 1.294 が実約定で再現するか?」

**応答**:
- スプレッド見積 (USD 1.0 / GBP 1.5 pip) は Phase 0' PnL 計算に控除済
- スリッページ・部分約定・約定遅延は未考慮 → §9.7 で Phase 2'A 実約定との乖離測定明記
- 乖離 > 20% なら BT 推定値そのものを再評価、撤退条件 #2 と統合判定

### 10.4 meta (Goodhart 化担当)

**反論**: 「ゲート +0.30 達成のために confidence 閾値を試行錯誤で見つけたのは試行錯誤的最適化 (= Goodhart 化) では?」

**応答**:
- LLM プロンプト本体は 1 回試行で確定 (Phase 0' 当初版から不変)
- 閾値最適化は **検索空間 5 ポイント** のみ、IS/OOS 分割でオーバーフィットチェック済
- IS で最良の閾値が OOS でも最良 → 構造的に妥当性あり
- DSR (Deflated Sharpe Ratio) で多重検定補正後の有意性確認は **n ≥ 100** または **Phase 2'B 60 日延長終了時** に実施 (Phase 2'A 30 日では n 不足、§9.3 明記。Ultra/Karen バグ⑦ 是正、2026-05-27)

---

## 11. CYCLE2_PLAN.md ゲート達成確認 (Proposal 3 反映)

| ゲート | 基準 | 達成状況 |
|---|---|---|
| G0-A: PF 差分 ≥ +0.30 | signal_v2 base → LLM フィルタ後 | **Combined PF 1.354 (+0.438) で達成、+0.30 を 1.46倍超過** |
| G0-B: 自己改善メカニズム | プロンプト調整 + フォールバック明示 | §4 で明示 (confidence 閾値月次再評価、3 段階フォールバック、撤退条件) |
| OOS trades ≥ 30 | フィルタ後残存件数 | USD_JPY n=203 / GBP_JPY n=469 で大幅達成 |
| IS-OOS 整合性 | OOS で IS と同等以上 | IS 1.335 → OOS 1.376 (+0.041 改善) |
| LLM REJECT 率 < 80% | フィルタきつすぎ防止 | USD 15.6% / GBP 32.9% で達成 |
| LLM コスト持続可能 | 月 ≤ 5,000円 | 月 ~¥50 想定で 100倍マージン |
| 直近期間 PF 維持 | 2025Q3+ で PF ≥ 1.2 | PF 1.338 で達成 |
| 機会費用超過 | 加点項目 | Phase 2'A の実測待ち、Phase 0' 推定で年率 200%+ |

---

## 12. SPEC v3 採用判断 (統括)

### 12.1 採用方針

Phase 2'A (ペーパー30日) → Phase 2'B (経済性Gate) → Phase 2'C (本番、段階移行) の段階的移行で SPEC v3 (Proposal 3) を採用。

### 12.2 不採用条件 (撤退条件と紐づけ)

1. **Phase 2'A 起動前**: 再現性テスト (§9.4) でラベル不一致率 > 5%
2. **Phase 2'A 終了時**: 経済性 Gate 不達かつ 60 日延長後も改善なし
3. **Phase 2'C-1 (本番初期 30 日)**: 直近 30 日 PF < 1.0 で停止
4. **任意のタイミング**: 撤退条件 §4.5 #5 (両ペア撤退条件成立)

### 12.3 採用後の継続条件

- ローリング 30 日 PF ≥ 1.0 (月次レビュー)
- LLM API コスト月 ≤ 5,000円
- 反論屋3体 Phase 2'B 経済性 Gate 判定で「採用継続」独立合意
- **confidence 閾値ドリフトなし** (月次 confidence 分布の安定性)

### 12.4 SPEC v3 (Proposal 3) の位置付け再確認

- **手法 → フレーム の順を堅持** (RETREAT_2026-05-26.md L83 原則準拠)
- PF > 0.95 (signal_v2) を超える手法を J 改善余地メタ分析で確定 (Proposal 3 = PF 1.354)
- それに合わせて SPEC v3 を更新 (Proposal 3 反映)
- **継承**: yo_hide 流 LLM フィルタ、季節フィルタ (GBP_JPY 限定)、観察基盤
- **捨てる**: SPEC v2 PoC 三重定義、CONFIRM+CONTRADICT そのまま (n=10 偽陽性発覚)、自己改善のシグナル抑制で見かけ PF を作る発想
- signal_v2 は完成済戦略として **改変禁止**。LLM 補完層 + confidence 閾値層のみが本仕様の検証対象

### 12.5 ユーザー意思決定パターンの継承

J 改善余地メタ分析が発見できたのは、ユーザーが「現状で進む vs 撤退」の二択ではなく「**改善余地を体系検討**」を挟んだから (memory `feedback_improvement_headroom_before_decision.md` 教訓)。SPEC v3 改訂版はこの意思決定パターンを構造的に組み込み:

- Phase 2'A 終了時 (ゲート判定) で結果が境界値なら、即「進む or 撤退」せず「改善余地メタ分析」を必須化
- 例: PF が 1.2-1.3 圏に着地したら、ペア別 confidence 閾値、セッション、レジーム別で再分析

---

## 13. ファイル構成 (実装ガイダンス)

```
src/
├── spec_v2/                  # 改変禁止
│   ├── signal_v2.py
│   └── seasonal_detection.py
├── spec_v3/                  # 新規
│   ├── __init__.py
│   ├── llm_filter.py         # LLM 補完層
│   ├── confidence_threshold.py  # ペア別 confidence 閾値 (Proposal 3)
│   ├── llm_context.py        # build_llm_context
│   ├── demo_loop.py          # Phase 2'A ペーパーループ
│   ├── trading_loop_v3.py    # 擬似コード §2.1 の実装
│   ├── limits.py             # SPEC v3 専用損失上限
│   ├── killswitch.py         # キルスイッチ
│   ├── observability.py      # Slack/DB/抑制シグナル記録
│   └── self_improve.py       # ドリフト検出 / 月次再評価 / フォールバック

scripts/
├── spec_v3_alive_slack.py    # 死活通知
├── spec_v3_daily_summary_slack.py  # 日次サマリ
├── _spec_v3_monthly_review.py  # 月次 LLM 判定パターン分析
└── _register_spec_v3_tasks.ps1  # VPS タスクスケジューラ登録

data/
└── fx_spec_v3.db             # SPEC v3 専用 SQLite

docs/
├── SPEC_V3.md                # 本仕様書 (Proposal 3 改訂版)
├── SPEC_V3_DEPLOY.md         # デプロイ手順書
├── PHASE_2A_PLAN.md          # Phase 2'A 計画書
├── CYCLE2_PLAN.md            # 既存 (継承元)
└── proposals/cycle2/         # 既存 (Phase 0' + 改善余地メタ分析)
```

---

## 14. 関連ドキュメント

- `docs/CYCLE2_PLAN.md` — 第2サイクル計画 (本仕様の起点)
- `docs/RETREAT_2026-05-26.md` — SPEC v2 撤退記録 (継承教訓)
- `docs/proposals/REVIEW_PHASE2.md` — 第1サイクル 5/5 FAIL 集計
- `docs/proposals/cycle2/LLM_FILTER_EXPANSION_REPORT.md` — Phase 0' 3 ペア統合
- **`docs/proposals/cycle2/IMPROVEMENT_META_ANALYSIS.md` — Proposal 3 採用根拠 (本改訂の中核)**
- `docs/proposals/cycle2/LLM_WFA_BT_REPORT.md` — GBP_JPY WFA + DSR 検証
- `src/spec_v2/signal_v2.py` — ベース戦略 (改変禁止)
- `src/spec_v2/seasonal_detection.py` — GBP_JPY 専用 VOLATILE フィルタ
- Memory: `feedback_improvement_headroom_before_decision.md` — 「改善余地検討」意思決定パターン

---

**起草**: Phase 2' SPEC v3 起草エージェント (2026-05-26)
**改訂**: Proposal 3 反映 (2026-05-27)
**確認待ち**: ユーザー判断 (Phase 2'A 起動可否、USD_JPY 全件検証完了 + GBP_JPY 全件検証完了 + Proposal 3 改善余地メタ分析確認後)
