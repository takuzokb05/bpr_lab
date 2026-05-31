# 次回セッション タスク整理 — Phase 2'A 起動 + 運用

> **作成日**: 2026-05-30
> **直前状態**: Phase 2'A 起動準備完了、3反論屋 2/2 起動 OK (Ultra 自己提案で karen+pragmatist のみ)、ユーザー最終承認待ち
> **次回エントリーポイント**: 本ファイル + `STATUS.md` + `docs/SPEC_V3_DEPLOY.md`

---

## 🎯 Phase 1: VPS 起動 (次回最初、30分〜1時間)

### 1.1 起動前最終確認

- [ ] **branch 確認**: `feature/proposal-selection` が最新 (latest commit: `0d1831b` H-①/③/④/⑤ + `4c9c829` H-②)
- [ ] **ローカル dry-run**: `python -m src.spec_v3.demo_loop --dry-run --single-iter` で 1 イテレーション動作確認
  - MT5 接続成功 (Mt5Client.init)
  - signal_v2 シグナル生成 (no_signal でも OK、エラーなければ)
  - LLM フィルタ呼び出し (dry-run なら DRY_RUN 記録のみ)
  - DB 書き込み成功 (`data/fx_spec_v3.db`)
  - Slack 通知届く (Webhook 設定済の場合)
- [ ] **テスト全件 PASS 再確認**: `pytest tests/spec_v3/ -v` で 45/45 PASS

### 1.2 VPS デプロイ (詳細は `docs/SPEC_V3_DEPLOY.md`)

```powershell
# VPS で実行
ssh vps
cd C:\bpr_lab_spec_v2\sandbox\FX自動取引

# 1. 旧 SPECv2 タスクが Disabled 維持を確認
Get-ScheduledTask | Where-Object { $_.TaskName -like "SPECv2*" } | Format-Table TaskName, State

# 2. 最新コード取得
git pull --ff-only origin feature/proposal-selection

# 3. .env 確認 (ANTHROPIC_API_KEY, SPEC_V3_SLACK_WEBHOOK_URL)
Get-Content .env | Select-String "ANTHROPIC_API_KEY|SPEC_V3_SLACK_WEBHOOK"

# 4. dry-run で接続確認 (VPS でも実施)
python -m src.spec_v3.demo_loop --dry-run --single-iter

# 5. タスクスケジューラ登録 (3 タスク)
.\scripts\_register_spec_v3_tasks.ps1

# 6. 起動
Start-ScheduledTask -TaskName "SPECv3_Demo"

# 7. 動作確認 (Slack 起動通知届くか、Get-ScheduledTaskInfo)
Get-ScheduledTaskInfo -TaskName "SPECv3_Demo"
```

### 1.3 起動直後チェック (30分以内)

- [ ] Slack #ai-alerts に起動通知届いた
- [ ] `data/fx_spec_v3.db` に loop_health 行が記録された
- [ ] 1時間以内に死活通知 (`SPECv3_AliveCheck`) 届く
- [ ] エラーログなし (`data/spec_v3_demo.log` tail)

---

## 🔄 Phase 2: 30日デモ運用 (2026-05-30 〜 2026-06-29)

### 2.1 日次観察 (毎朝 JST 07:00)

- [ ] Slack 日次サマリで以下を確認:
  - 取引件数 (想定: USD_JPY ~8-12 / GBP_JPY ~20-25 / 月)
  - confidence 分布 (≥閾値 採用 vs 未達 除外)
  - PF (累計) / 勝率 / PnL
  - LLM API コスト (月 ¥5,000 上限の何 %)
  - キルスイッチ発火 (異常時のみ)
  - **撤退条件チェック** (近接ありで警告)

### 2.2 週次レビュー (毎週日曜 JST 21:00)

- [ ] 抑制シグナル群の仮想 PnL 集計
- [ ] 想定取引件数との乖離
- [ ] ペア別パフォーマンス推移

### 2.3 Phase 2'A 開始 1-2週間以内の追加実装 ⭐

**Pragmatist 警告対応**: 撤退条件 #0 (lift ベース) を機能化する。

- [ ] **`scripts/_spec_v3_suppressed_pnl.py` 作成** (Pragmatist 警告 1)
  - `llm_judgments.accepted=0` 行 (抑制シグナル) に対し、24h 後の高安値で仮想 PnL を計算
  - 結果を `signal_v2 抑制群実 PnL` として DB に保存
  - `KillSwitchState.compute_lift_per_pair()` が base PF を計算できるようになる
- [ ] **月次タスクスケジューラ登録** (`scripts/_register_spec_v3_suppressed_pnl_monthly.ps1` 作成)

### 2.4 Phase 2'A 開始 2週間以内に確認

- [ ] **spread_baseline 永続化フック** (Ultra E節盲点1): heartbeat 時の `_persist_killswitch_state` 呼び出し追加
- [ ] **ATR 分布 KS 検定** (Ultra F節): `llm_judgments.atr` 分布 vs Phase 0' BT `atr` 分布の KS test (1週間運用後にスクリプト作成)

---

## 🚪 Phase 3: Phase 2'B 経済性 Gate 判定 (Phase 2'A 終了時、2026-06-29 想定)

### 3.1 ゲート判定 (必須全 PASS)

| ゲート | 基準 | 不達時 |
|---|---|---|
| PF (累計) | ≥ 1.30 | 60 日延長 |
| Sharpe (年率) | ≥ 0.8 | 60 日延長 |
| MaxDD | ≤ 15% | 60 日延長 |
| OOS trades | USD ≥ 8 / GBP ≥ 20 | 延長 |
| LLM コスト累計 | ≤ 5,000 円/月 | 撤退条件 #4 |
| Phase 0' BT 乖離 | 実約定 PF と BT PF の乖離 ≤ 20% | BT 推定値再評価 |
| **confidence AUC (採用群)** | **≥ 0.55 (ペア別)** | **confidence 閾値ロジック見直し** |

> **AUC gate の根拠** (2026-05-31 追加): Phase 0' BT データで confidence 判別力を実測したところ USD_JPY AUC=0.51 (コイン投げ)・GBP_JPY 0.54。「confidence≥閾値で絞る」中核メカニズムが特に USD で機能していない疑い。PF だけで通した過去の盲点を塞ぐため、実約定 AUC を PF と並ぶ必須 gate に追加。測定: `scripts/_spec_v3_confidence_calibration.py`、日次監視: `spec_v3_daily_summary_slack.py`。詳細 memory [[feedback_confidence_auc_not_pf]] / `docs/analysis/LLM_ADVISORY_EXTERNAL_RESEARCH.md`。

### 3.2 反論屋3体 (karen / ultrathink / pragmatist) 起動再判定

- [ ] Phase 2'B Gate 判定時に **反論屋3体合意** 必須 (PHASE_2A_PLAN.md §10.5)

### 3.3 Phase 2'C (本番) 進入判断

- 全 Gate PASS + 反論屋合意 → Phase 2'C-1 (本番 lot 0.01 × 30日)
- 不達 → Phase 2'A 60日延長 or 撤退

---

## 📋 残課題リスト (低優先度、Phase 2'A 中 or 後)

| 課題 | 優先度 | 期限 |
|---|---|---|
| `_spec_v3_suppressed_pnl.py` 作成 (lift 撤退条件機能化) | **中** | Phase 2'A 開始 2週間以内 |
| spread_baseline 永続化フック | 低 | Phase 2'A 中 |
| ATR 分布 KS 検定 | 低 | Phase 2'A 1週間後 |
| close_all_positions 部分失敗ハンドリング詳細 | 低 | Phase 2'B 前 |
| `branch 名` 整理 (gitステータス表示混乱) | 軽微 | 任意 |

---

## 🚨 緊急時対応

### 撤退条件 #1-3 発火 (当該ペア停止)
- 90日 trades<5 / 直近100 trades PF<1.0 / 累計-3,000 JPY
- → 当該ペア自動停止、Slack 警告、人手レビュー

### 撤退条件 #4 発火 (LLM 月コスト > ¥5,000)
- → LLM 層退避 (signal_v2 単独運用に切替)

### 撤退条件 #5 発火 (両ペア #1-3 同時成立)
- → SPEC v3 全体停止、`close_all_positions` 実行、Slack 警告

### Black Swan (人手判断停止)
- 1日 -10% 超 / LLM 判定異常 (CONFIRM 率 90%+ 連続) / 反論屋3体中 2 体停止判定
- → 緊急手動停止: `Stop-ScheduledTask -TaskName "SPECv3_Demo"; Disable-ScheduledTask -TaskName "SPECv3_Demo"`

---

## 🔗 参照ドキュメント

- `STATUS.md` — 現状ダッシュボード
- `docs/SPEC_V3.md` — 仕様 (Proposal 3 改訂版)
- `docs/PHASE_2A_PLAN.md` — Phase 2'A 計画
- `docs/SPEC_V3_DEPLOY.md` — VPS デプロイ手順
- `docs/proposals/cycle2/STANDARD_SPLIT_REANALYSIS.md` — 経済性根拠 (M2)
- `docs/analysis/PHASE2A_REVIEW3_*.md` — 反論屋3回目最終査読 (起動 OK 2/2)
- Memory: `feedback_ultra_iterative_bug_discovery.md`, `feedback_meta_analysis_split_selection_bias.md`, `feedback_spec_bt_impl_three_layer_check.md`

---

## 次回再開時の最短手順

1. **本ファイル (NEXT_SESSION_TASKS.md) を最初に読む**
2. **STATUS.md で現状確認** (前回終了時点)
3. **Phase 1.1 起動前最終確認** から着手
4. dry-run 成功で **Phase 1.2 VPS デプロイ** → 起動

すべて準備完了、ユーザーの GO サイン待ち状態。

---

**起草**: 2026-05-30、Claude Code セッション終了に向けた整理
