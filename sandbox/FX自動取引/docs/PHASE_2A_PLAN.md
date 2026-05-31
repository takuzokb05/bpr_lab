# Phase 2'A 計画書 — VPS デモ運用 30日

> **起草日**: 2026-05-27
> **目的**: SPEC v3 (Proposal 3 確定版) の **実運用検証** をデモ口座 30日で実施
> **前提**: Phase 0' BT で USD_JPY PF 1.565 / GBP_JPY PF 1.294 / Combined PF 1.354 達成 (`docs/proposals/cycle2/IMPROVEMENT_META_ANALYSIS.md`)
> **根拠**: `docs/SPEC_V3.md` (Proposal 3 改訂版) / `docs/CYCLE2_PLAN.md` / `docs/RETREAT_2026-05-26.md`

---

## 0. 計画の目的と非目的

### 目的
1. Phase 0' BT (PF 1.354) が **実運用で再現するか** 検証
2. **スリッページ・約定遅延・スプレッド変動** の実体測定
3. **LLM 判定の安定性** (temperature=0 でも非完全保証) 観察
4. **撤退条件の妥当性** 確認 (撤退条件は実際に運用してみないと適切な閾値が分からない)

### 非目的
- 本番投入 (Phase 2'C) — Phase 2'B 経済性 Gate 通過後
- 新戦略開発 — SPEC v3 で確定済
- パラメータチューニング — Phase 0' で確定、運用中変更禁止

---

## 1. 運用構成

| 項目 | 値 |
|---|---|
| 環境 | VPS Windows Server 2025 (160.251.221.43) |
| ブローカー | 外為ファイネスト MT5 デモ口座 22005467 |
| 残高 | 1,000,000 JPY (デモ) |
| 対象ペア | USD_JPY (主) + GBP_JPY (副) |
| 戦略 | signal_v2 + LLM フィルタ + ペア別 confidence 閾値 |
| ロット | **0.01 固定** (lot 0.01 = 1,000 units、10 JPY/pip) |
| 最大保持時間 | 24 時間 |
| 同時ポジション | 1 ペア 1 ポジション、全体最大 2 |
| LLM モデル | Claude Sonnet 4.6 (Anthropic API、本番運用は API キー直叩き許可) |
| Confidence 閾値 | USD_JPY ≥ 0.65、GBP_JPY ≥ 0.60 |
| 期間 | **30 日連続稼働** (中断時は再起動から 30 日リセット) |

---

## 2. 起動前チェックリスト

### 2.1 必須前提

- [x] SPEC_V3.md を Proposal 3 で改訂済 ✅ (2026-05-27)
- [x] M1 (実装層バグ②③⑤⑥修正)、M2 (標準分割再分析)、M1b (整合修正) 完了 ✅ (2026-05-27)
- [ ] `src/spec_v3/` 実装と SPEC v3 の整合性最終確認 (VOLATILE フィルタなしで一致)
- [ ] `data/fx_spec_v3.db` 初期化 (SPEC v2 DB と分離)
- [ ] VPS タスクスケジューラ `FX_SPEC_V3_PAPER` 登録 (ExecutionTimeLimit=PT0S)
- [ ] Slack Webhook 動作確認 (#ai-alerts チャンネル)
- [ ] 旧 `SPECv2_PoC` 系タスクが Disabled 状態のまま (干渉防止)
- [ ] **スプレッド異常 baseline 確立期間** (起動後 数時間〜半日) の認識共有 (この期間は異常検知が発火しない誤発火防止設計)

### 2.2 必須検証

- [ ] **LLM 再現性テスト**: 同一入力で 5 回判定、ラベル不一致率 < 5% / confidence ブレ < 0.1
- [ ] **dry-run 動作確認**: `python -m src.spec_v3.demo_loop --dry-run` で MT5 接続 + LLM 判定 + DB 書き込みが動く (発注なし)
- [ ] **キルスイッチ動作確認**: VIX > 30 シミュ、スプレッド 3倍シミュ、LLM API 失敗シミュ で停止すること
- [ ] **死活監視動作確認**: タスクスケジューラから手動起動 → Slack 通知届くこと

### 2.3 反論屋呼び出し (SPEC v3 §10.5 必須)

Phase 2'A 起動前に **反論屋3体 (karen / ultrathink-debugger / code-quality-pragmatist)** を独立に呼び出し、起動 OK で 3/3 揃わなければ起動延期:

1. **karen**: 「Proposal 3 の閾値選定で Goodhart 化していないか?」
2. **ultrathink-debugger**: 「SPEC v3 の三層構造 (signal_v2 / LLM / 閾値) は構造的に妥当か?」
3. **code-quality-pragmatist**: 「Phase 0' PF 1.354 が実約定で再現する見込みは?」

---

## 3. 観察項目 (日次・週次・月次)

### 3.1 日次サマリ (Slack #ai-alerts、JST 07:00)

```
SPEC v3 Phase 2'A Day {N}/30 — YYYY-MM-DD

USD_JPY (主):
  Signal生成: N1 / LLM判定済: N2 / 発注: N3
  confidence 分布: ≥0.65 採用 X件 / 0.5-0.65 除外 Y件
  PF (累計): Y.YY / 勝率: X.X% / PnL: ±N JPY
  オープン: N件 (entry @ p1, p2, ...)

GBP_JPY (副):
  Signal生成: N1 / LLM判定済: N2 / 発注: N3
  confidence 分布: ≥0.60 採用 X件 / 0.5-0.60 除外 Y件
  PF (累計): Y.YY / 勝率: X.X% / PnL: ±N JPY
  オープン: N件

LLM API コスト: 当日 $X.XX / 累計 $X.XX (月 ¥XXX、上限 ¥5,000)
キルスイッチ: 0件 (or 件数+詳細)
撤退条件チェック: 全 PASS (or 接近条件)
ローリング 30日 PF: USD_JPY=Y.YY / GBP_JPY=Y.YY
```

### 3.2 死活監視 (1時間ごと)

- signal_v2 が直近 1 時間に何件出したか
- LLM API 連続失敗回数
- 直近 100 件の confidence 平均値
- MT5 接続状態

### 3.3 週次レビュー (毎週日曜 JST 21:00、Slack)

- 抑制シグナル群の仮想 PnL 集計 (「取らなかったことが正解か」)
- confidence 閾値未達 (CONFIRM だが conf 不足) の trades 数と理論 PnL
- 想定取引件数との乖離
- ペア別パフォーマンスの推移

### 3.4 月次レビュー (月末、Slack + memo)

- LLM 判定パターン分析 (CONFIRM/NEUTRAL/CONTRADICT/REJECT 比率の月次変化)
- confidence 分布の安定性
- Phase 0' BT 1.354 との実約定 PF 乖離測定

---

## 4. ゲート判定 (Phase 2'B 進入基準)

Phase 2'A 終了 (30日後 or 60日延長後) に以下のゲートで Phase 2'C (本番投入) 進入可否判定:

### 4.1 必須ゲート (全 PASS 必要)

| ゲート | 基準 | 不達時の行動 |
|---|---|---|
| **PF (累計)** | ≥ 1.30 | 60 日延長 → 改善なければ撤退条件 #2 統合判定 |
| **Sharpe (年率換算)** | ≥ 0.8 | 同上 |
| **MaxDD** | ≤ 15% | 同上 |
| **OOS trades** | USD_JPY ≥ 8 / GBP_JPY ≥ 20 | サンプル不足、Phase 2'A 延長 |
| **LLM API コスト累計** | ≤ 5,000 円 (月換算) | 撤退条件 #4 発動 |
| **Phase 0' BT 乖離** | 実約定 PF と BT PF の乖離 ≤ 20% | BT 推定値再評価、閾値再最適化 |
| **confidence AUC (採用群、ペア別)** | **≥ 0.55** | confidence 閾値ロジック見直し |

**AUC gate 追加背景** (2026-05-31): Phase 0' BT で confidence 判別力を実測したところ USD_JPY AUC=0.51 (コイン投げ)・GBP_JPY 0.54。「confidence≥閾値で絞る」中核メカニズムが特に USD で機能していない疑い。PF だけで採否を決めた過去の盲点 (memory `feedback_confidence_auc_not_pf`) を塞ぐため、実約定 AUC を必須 gate 化。日次監視は `spec_v3_daily_summary_slack.py`、正式測定は `scripts/_spec_v3_confidence_calibration.py --source db`。外部裏付け `docs/analysis/LLM_ADVISORY_EXTERNAL_RESEARCH.md`。

### 4.2 加点ゲート (満たすと Phase 2'C 確信度高)

| 項目 | 基準 | 評価タイミング |
|---|---|---|
| Sortino | ≥ 1.0 | Phase 2'A 終了時 (n=30-40) |
| Deflated Sharpe Ratio | ≥ 0.5 | **n ≥ 100 または Phase 2'B 60 日延長終了時** (Ultra/Karen バグ⑦ 是正、2026-05-27) |
| 連敗最長 | ≤ 5 | Phase 2'A 終了時 |
| キルスイッチ動作回数 | 0-2 件 (適切な発火) | Phase 2'A 終了時 |
| 経済指標発表時の挙動 | 大損失なし | Phase 2'A 終了時 |

**DSR 評価条件の修正背景** (2026-05-27):
- 当初: Phase 2'A 終了時 (30 日 / n=30-40) に DSR ≥ 0.5 を評価する予定
- 是正: 30 日 n=30-40 では多重検定補正に必要なサンプル不足。Phase 2'B 60 日延長または実約定 n ≥ 100 時点まで延期
- 代替: Phase 2'A 30 日では IS/OOS 乖離 ≤ 20% を多重検定リスクの代替評価とする

### 4.3 即時棚上げ (FAIL)

- 必須ゲートのいずれか 1 つでも FAIL
- 撤退条件 §4.5 の 1-3 が発火
- Black Swan 事象で MaxDD > 20% 発生

---

## 5. Black Swan 監視 (RETREAT 教訓継承)

### 5.1 監視対象事象

| 事象例 | 検知 | 対応 |
|---|---|---|
| VIX 急騰 (> 30) | yfinance 5分ポーリング | 全ペア新規停止 |
| 円介入 (USD/JPY 1日 ±2%超) | 日次集計 | 当該ペア新規停止 24h |
| 経済指標サプライズ (NFP, CPI, FOMC, BOJ) | 経済指標カレンダー事前検知 | 発表前後 30分新規停止 |
| Brexit-class イベント | 1日±3σ 急変検知 | 全ペア停止 + 反論屋緊急レビュー |

### 5.2 ストレステスト指標

Phase 2'A 期間中に過去類似ストレス事象 (例: 円介入懸念、米利下げ転換、英 BoE 政策) が発生した場合の挙動を必ず記録。

---

## 6. 撤退条件 (SPEC v3 §4.5 継承)

### 6.1 当該ペア停止 (条件 0-3)

- **0. lift vs base < +0.30 が 3 ヶ月連続** (M2 提案で追加、2026-05-27、SPEC §4.5 #0 と整合)
- 1. 90日 trades < 5
- 2. 直近 100 trades で PF < 1.0 維持
- 3. 累計 -3,000 JPY (lot 0.01)

**lift の計算**: ローリング 30 日 PF (CONFIRM 採用群) − ローリング 30 日 base PF (LLM 無視全件)。

**lift ベース条件 #0 の意味**: 絶対値 PF が市況変動で揺れても、base 比 +0.30 維持 = LLM フィルタの「付加価値」を継続評価できる安定指標 (M2 16 分割で lift σ=0.04 と立証済)。

### 6.2 LLM 層退避 (条件 4)

- LLM API 月コスト > 5,000円
- → signal_v2 + 季節フィルタ (GBP_JPY) のみで運用継続

### 6.3 SPEC v3 全体停止 (条件 5)

- 両ペアで条件 1-3 が同時成立
- Phase 2'B 経済性 Gate で 60 日延長後も不達

### 6.4 緊急停止 (人手判断)

- Black Swan 事象で 1 日 -10% 超
- LLM 判定が明らかに異常 (例: CONFIRM 率 90%+ 連続)
- 反論屋3体の中で 2 体以上が「停止」判定

---

## 7. デモ→本番移行 (Phase 2'C 前提)

### 7.1 Phase 2'B 経済性 Gate 通過 (§4.1 全 PASS)

→ Phase 2'C 進入

### 7.2 Phase 2'C 段階移行

| ステップ | lot | 期間 | 進入ゲート |
|---|---|---|---|
| 2'C-1 | 0.01 | 30 日 | 直近 30 日 PF ≥ 1.2 で 2'C-2 へ |
| 2'C-2 | 0.02 | 30 日 | 同上 |
| 2'C-3 | ATR ベース可変 (元本 1% リスク) | 継続 | ローリング 30 日 PF < 1.0 で半量化 |

各ステップ移行は **Slack ユーザー確認必須** (自動進行禁止)。

---

## 8. 起動・運用手順

### 8.1 起動コマンド (VPS)

```powershell
# 1. dry-run で接続確認
python -m src.spec_v3.demo_loop --dry-run

# 2. 本起動 (タスクスケジューラから)
Start-ScheduledTask -TaskName "FX_SPEC_V3_PAPER"

# 3. 死活確認
Get-ScheduledTaskInfo -TaskName "FX_SPEC_V3_PAPER"
```

### 8.2 緊急停止コマンド

```powershell
# 1. タスク停止
Stop-ScheduledTask -TaskName "FX_SPEC_V3_PAPER"
Disable-ScheduledTask -TaskName "FX_SPEC_V3_PAPER"

# 2. プロセス強制終了
Stop-Process -Name "python" -Force

# 3. オープンポジションの確認 + 手動クローズ (必要なら)
```

### 8.3 観察 URL

- Slack #ai-alerts (日次サマリ + 死活)
- VPS タスクスケジューラ (FX_SPEC_V3_PAPER の状態)
- ローカル `data/fx_spec_v3.db` (毎日 git pull で同期)

---

## 9. 既知のリスクと対策

### 9.1 LLM API レート制限

- Anthropic API のレート制限に当たる可能性 (大量シグナル発生時)
- **対策**: 1秒1リクエスト程度に抑える + リトライ機構 (指数バックオフ 3回)

### 9.2 MT5 接続切断

- VPS 再起動 / ブローカー側保守で MT5 接続断
- **対策**: 接続再試行ロジック + Slack 警告 + キルスイッチ作動 (LLM API 障害と同等扱い)

### 9.3 Phase 0' BT 乖離

- スリッページ・部分約定で実約定 PF が 1.35 → 1.10 等に劣化する可能性
- **対策**: 月次乖離測定、20% 超で BT 推定値再評価

### 9.4 LLM モデル更新

- Sonnet 4.6 → 4.7 で confidence 校正変化
- **対策**: モデル更新前に既存データで再判定、confidence 分布シフト > 0.1 なら閾値再最適化

### 9.5 デモと本番の市況差

- デモ口座は本番より約定優位な場合あり (スプレッド・スリッページ)
- **対策**: Phase 2'C-1 (本番初期 30 日) で再度乖離測定

---

## 10. 関連ドキュメント

- `docs/SPEC_V3.md` — 仕様書 (Proposal 3 改訂版)
- `docs/CYCLE2_PLAN.md` — 第2サイクル計画 (起点)
- `docs/RETREAT_2026-05-26.md` — SPEC v2 撤退教訓 (継承)
- `docs/proposals/cycle2/IMPROVEMENT_META_ANALYSIS.md` — Proposal 3 採用根拠
- `docs/SPEC_V3_DEPLOY.md` — VPS デプロイ手順 (K2 実装後)
- Memory: `feedback_improvement_headroom_before_decision.md` — 「改善余地検討」意思決定パターン

---

## 11. 起動承認フロー

Phase 2'A 起動には以下の **3 段階承認** が必要:

1. **K2 (デプロイ実装) 完了** — `src/spec_v3/` 実装 + dry-run PASS
2. **反論屋3体合意** — karen / ultrathink-debugger / code-quality-pragmatist が独立に「起動 OK」
3. **ユーザー最終承認** — 上記2つを踏まえてユーザーが Phase 2'A 起動可と判断

承認が揃ったら VPS で `Start-ScheduledTask -TaskName FX_SPEC_V3_PAPER` を実行。

---

**起草**: 2026-05-27
**確認待ち**: K2 完了 + 反論屋呼び出し + ユーザー判断
