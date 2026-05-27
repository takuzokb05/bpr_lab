# SPEC v3 デプロイ手順書 — VPS デモ運用

> **対象**: Phase 2'A (VPS Windows Server 2025、MT5 デモ口座 22005467)
> **目的**: SPEC v3 Demo Loop (Proposal 3) を 30 日連続稼働させる
> **関連**: `docs/SPEC_V3.md`, `docs/proposals/cycle2/IMPROVEMENT_META_ANALYSIS.md`

---

## 前提

| 項目 | 値 |
|---|---|
| VPS | ConoHa Windows Server 2025 (160.251.221.43) |
| Python | `C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe` |
| リポジトリ clone 先 | `C:\bpr_lab_spec_v2\sandbox\FX自動取引` |
| MT5 ターミナル | 外為ファイネスト、ログイン済み (デモ 22005467) |
| ブランチ | `feature/spec-v2-rebuild`（マージ後は `main`） |

## 0. 旧運用の停止確認

```powershell
# SPEC v2 PoC タスクが Disabled か確認
Get-ScheduledTask -TaskName "SPECv2_*" | Format-Table TaskName, State
# 全部 Disabled でなければ:
Stop-ScheduledTask  -TaskName "SPECv2_PoC" -ErrorAction SilentlyContinue
Disable-ScheduledTask -TaskName "SPECv2_PoC"
```

`_register_spec_v3_tasks.ps1` も冒頭で旧タスクを止めるが、念のため事前確認推奨。

---

## 1. コード反映 (VPS)

```powershell
ssh vps
cd C:\bpr_lab_spec_v2\sandbox\FX自動取引

# pull-only ルール (feedback_vps_git_hygiene.md)
git fetch origin
git checkout feature/spec-v2-rebuild   # マージ後は main
git pull --ff-only

# 新規ファイル確認
Get-ChildItem src\spec_v3, scripts\spec_v3_*, scripts\_register_spec_v3_tasks.ps1
```

---

## 2. 環境変数

`.env` に追記 (チャット欄ではなく直接エディタで):

```
# SPEC v3 専用 Webhook (推奨)。未設定なら SLACK_ALERTS_WEBHOOK_URL → SLACK_WEBHOOK_URL の順に fallback
SPEC_V3_SLACK_WEBHOOK_URL=

# Anthropic API キー (LLM filter 用)
ANTHROPIC_API_KEY=
```

VPS で確認:

```powershell
code .env
# SPEC_V3_SLACK_WEBHOOK_URL と ANTHROPIC_API_KEY が空でないこと
```

---

## 3. 依存パッケージ

`requirements.txt` に既に含まれている前提だが、念のため:

```powershell
& $env:LOCALAPPDATA\Programs\Python\Python313\python.exe -m pip install --upgrade `
    MetaTrader5 anthropic pandas python-dotenv requests numpy
```

---

## 4. ローカル動作確認 (dry-run)

VPS でいきなり常駐させず、まず `--dry-run --single-iter` で接続確認:

```powershell
cd C:\bpr_lab_spec_v2\sandbox\FX自動取引
& "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe" `
    -m src.spec_v3.demo_loop --dry-run --single-iter
```

期待出力:
- "SPEC v3 デモループ開始" のヘッダ
- MT5 接続成功 (`Mt5Client` 経由で USD_JPY と GBP_JPY の M15 取得)
- LLM 呼び出しは dry-run のため skip (`DRY_RUN` ラベルが DB に記録)
- "ループ停止 (iter_count=1)"

ログ: `data/spec_v3_demo.log`
DB: `data/fx_spec_v3.db` (テーブル llm_judgments / trades / loop_health / trade_closures / llm_api_cost_daily)

---

## 5. タスクスケジューラ登録

```powershell
cd C:\bpr_lab_spec_v2\sandbox\FX自動取引
.\scripts\_register_spec_v3_tasks.ps1
```

登録されるタスク:

| TaskName | 内容 | トリガー |
|---|---|---|
| **SPECv3_Demo** | デモループ常駐 (60 秒間隔) | AtStartup |
| **SPECv3_AliveCheck** | 死活監視 Slack 通知 | AtStartup + Once+RepetitionInterval=PT1H |
| **SPECv3_DailySummary** | 日次サマリ Slack 通知 | Daily JST 07:00 |

**重要設定** (PT72H 罠回避):
- `ExecutionTimeLimit = PT0S` (= 無制限)
- `MultipleInstances = IgnoreNew` (再起動時の二重起動防止)
- `RestartCount = 5, RestartInterval = PT5M` (失敗時自動再起動)

旧 SPEC v2 タスクは登録スクリプトで自動 Disable される。

---

## 6. 起動

```powershell
Start-ScheduledTask -TaskName "SPECv3_Demo"
Start-Sleep -Seconds 5

# プロセス確認
Get-ScheduledTask -TaskName "SPECv3_Demo" | Format-Table TaskName, State
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -or (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -match "spec_v3"
}
```

期待: `State=Running`、`python.exe` が `spec_v3.demo_loop` を引数で起動している。

死活も先行起動して動作確認:

```powershell
Start-ScheduledTask -TaskName "SPECv3_AliveCheck"
# Slack #ai-alerts に "SPEC v3 死活レポート" が届くこと
```

---

## 7. 30 日連続稼働の維持

### 7.1 確認すべき指標 (毎日)

毎朝 JST 07:00 の `SPECv3_DailySummary` Slack で確認:

- `LLM 判定分布`: CONFIRM/NEUTRAL/CONTRADICT/REJECT/API_ERROR の比率
- `per_pair`: trades 件数 / win_rate / PF / PnL
- `Rolling 100-trades PF`: 1.0 以上を維持
- `LLM コスト`: 月 5,000 円 (撤退条件 #4) に対する進捗
- `Retreat status`: `ok` 以外なら手動レビュー

### 7.2 死活アラート

`SPECv3_AliveCheck` は 1 時間毎に DB を見て、最新判定が 10 分以内なら ALIVE 扱い。
10 分超で Slack 警告 (赤)。`--quiet-when-alive` 指定により ALIVE 時は無音。

### 7.3 トラブルシュート

| 症状 | 対処 |
|---|---|
| `SPECv3_AliveCheck` が WARN | 1) MT5 ターミナル確認 / 2) `data/spec_v3_demo.log` 末尾確認 / 3) `Get-ScheduledTask SPECv3_Demo` State 確認 |
| LLM API 連続失敗 | キルスイッチ発火、`global_block_reason` 設定。`ANTHROPIC_API_KEY` 残量、ネットワーク確認 |
| PT72H で勝手に終了 | `_register_spec_v3_tasks.ps1` 再実行 (`ExecutionTimeLimit=PT0S` を再設定) |
| 撤退条件発火 | `data/fx_spec_v3.db` の `loop_health` テーブルから retreat イベントを確認 |

---

## 8. 撤退条件 (事前明文化、運用開始後の変更禁止)

| # | 条件 | 単位 | アクション |
|---|---|---|---|
| 1 | 90 日経過 + trades < 5 | 当該ペア | ペア停止 |
| 2 | 直近 100 trades の PF < 1.0 | 当該ペア | ペア停止 |
| 3 | 累計 PnL ≤ -3,000 JPY | 当該ペア | ペア停止 |
| 4 | LLM API 月コスト > 5,000円 (≒ $33) | システム | LLM 層無効化 |
| 5 | 1-3 が両ペアで成立 | システム | SPEC v3 全停止 |

ループ内で `run_all_safety_checks` が毎ループ実行され、撤退条件発火時は:
1. `loop_health` テーブルに `retreat` イベント記録
2. Slack 通知 (赤)
3. デイリーストップ以外はループ継続 (LLM 層無効化など軽量化のみ)
4. 撤退条件 #5 はループを break して停止

---

## 9. 停止 / ロールバック

```powershell
# ループを停止
Stop-ScheduledTask -TaskName "SPECv3_Demo"
Disable-ScheduledTask -TaskName "SPECv3_Demo"

# 死活/サマリも停止
Disable-ScheduledTask -TaskName "SPECv3_AliveCheck"
Disable-ScheduledTask -TaskName "SPECv3_DailySummary"

# プロセス強制終了 (必要時のみ)
Get-Process python | Where-Object {
    (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -match "spec_v3"
} | Stop-Process -Force

# DB はそのまま保持 (data/fx_spec_v3.db、検証用に残す)
# 完全に削除する場合のみ:
# Remove-Item data\fx_spec_v3.db
```

---

## 10. リリースチェックリスト

起動前に以下を確認:

- [ ] `git status` でローカルに差分が無い (VPS は pull-only)
- [ ] `.env` に `SPEC_V3_SLACK_WEBHOOK_URL` と `ANTHROPIC_API_KEY` が設定済
- [ ] `python -m src.spec_v3.demo_loop --dry-run --single-iter` でエラーなし
- [ ] `pytest tests/spec_v3/` がローカルで PASS
- [ ] MT5 ターミナルがログイン済 (デモ口座 22005467)
- [ ] 旧 SPECv2_* タスクが Disabled
- [ ] `_register_spec_v3_tasks.ps1` 実行後、3 タスクが Ready 状態
- [ ] `SPECv3_Demo` を Start して、5 分以内に `data/spec_v3_demo.log` に判定行が出る
- [ ] Slack #ai-alerts に死活レポートが届く

すべて OK なら Phase 2'A (30 日連続稼働) スタート。

---

## 関連メモ

- `feedback_task_scheduler_execution_time_limit.md` — PT72H 罠
- `feedback_vps_start_process.md` — ssh 越し Start-Process は使わない
- `feedback_vps_git_hygiene.md` — VPS は pull-only
- `feedback_mt5_volume_step.md` — MT5 volume_step 整列で retcode 10014 回避済 (`Mt5Client._adjust_volume`)
