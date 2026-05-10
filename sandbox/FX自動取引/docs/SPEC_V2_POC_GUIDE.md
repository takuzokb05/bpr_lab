# SPEC v2 PoC 運用ガイド (2026-05-11 起動)

> 明日朝から GBP_JPY デモ口座で動かすための起動・監視・停止ガイド。

## 構成 (確定)

| 項目 | 値 |
|---|---|
| 通貨ペア | GBP_JPY (単一) |
| 時間軸 | M15 + H1 二層判定 (D1 削除) |
| ループ間隔 | 60 秒 |
| ロット | 0.01 lot 固定 (= 1,000 units) |
| 最大保持時間 | 4 時間 (240 分、M15 16 本) |
| ポジション制限 | 1 |
| 口座 | デモ (MT5 22005467 / GaitameFinest-Demo) |
| DB | `data/fx_spec_v2.db` (亡き者と物理分離) |
| ログ | `data/spec_v2_poc.log` |
| Slack | 環境変数 `SPEC_V2_SLACK_WEBHOOK_URL` (任意) |

## 安全装置

1. **ロット固定 0.01** — risk_manager は流用しない、最小ロット
2. **1 ポジション制限** — 既存ポジションあれば新規エントリーしない
3. **時間損切り** — 4 時間で強制決済
4. **レジーム変化決済** — VOLATILE → CALM/TRANSITIONAL で全決済
5. **デモ口座限定** — 起動時に MT5 connect、デモ口座番号確認推奨

## エントリーロジック (placeholder, SPEC v2 § 3-1 確定まで仮)

1. SeasonalDetector が VOLATILE 判定 (M15 30%ile 超 + H1 0.00175 超 の **二層一致**)
2. M15 直近 20 本の最高値ブレイク → long、最安値ブレイク → short
3. SL = ATR(14) × 1.5、TP = ATR(14) × 3.0 (RR=2.0)

## 起動手順 (VPS 上)

### 環境メモ (VPS 確定)

- リポジトリ: `C:\bpr_lab_spec_v2` (worktree、亡き者の `C:\bpr_lab` と物理分離)
- 作業ディレクトリ: `C:\bpr_lab_spec_v2\sandbox\FX自動取引`
- Python: **`py -3.13`** で起動 (3.11 は numpy 不在、3.13 に numpy/pandas/pandas_ta/MetaTrader5 揃い)
- ブランチ: `feature/spec-v2-rebuild`

### 1. VPS 反映 (push 済みの前提)

```powershell
ssh vps
cd C:\bpr_lab_spec_v2
git pull
cd sandbox\FX自動取引
```

### 2. DB 初期化 (idempotent、初回のみ必要)

```powershell
py -3.13 -m src.spec_v2.db
```

期待出力: `DB initialized at: ...\data\fx_spec_v2.db`

### 3. ドライラン (動作確認、発注なし)

```powershell
# 1 イテレーションだけ (動作確認)
py -3.13 -m src.spec_v2.poc_loop --dry-run --single-iter

# 30 分程度しっかり走らせる (Ctrl+C で停止)
py -3.13 -m src.spec_v2.poc_loop --dry-run
```

#### 動作確認実績 (2026-05-10 17:55 JST)

```
[iter 1] regime=calm | M15 YZ=0.00025 thr=0.00031 above=False | H1 YZ=0.00050 thr=0.00175 above=False
```

- DB 初期化 / MT5 接続 / M15 5014 bars + H1 200 bars 取得 / 季節判定 / DB 書き込み すべて OK
- 1 イテレーションあたり ~1.4 秒

確認ポイント:
- `[iter N] regime=...` がログに出ること
- DB `seasonal_judgments` テーブルに 1 行ずつ追加されること
- エラーなく 30 分連続稼働すること
- (Slack 設定済なら) `🟢 PoC 起動` 通知が来ること

### 4. 本格起動 (デモ発注あり)

```powershell
py -3.13 -m src.spec_v2.poc_loop
```

- volatile 判定 + ブレイクアウトで 0.01 lot エントリー
- TP/SL ヒット or 4 時間 or レジーム変化で決済
- `data/fx_spec_v2.db` の `trades` / `trade_closures` に記録

### 5. タスクスケジューラ登録 (常駐化、推奨)

別タスクとして登録 (亡き者プロセス main.py とは別):

```powershell
$pyExe = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
$action = New-ScheduledTaskAction -Execute $pyExe -Argument "-m src.spec_v2.poc_loop" `
  -WorkingDirectory "C:\bpr_lab_spec_v2\sandbox\FX自動取引"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "SPECv2_PoC" -Action $action -Trigger $trigger
```

タスクスケジューラから手動起動: `Start-ScheduledTask -TaskName "SPECv2_PoC"`

## 停止手順

### 手動停止 (フォアグラウンド実行中)

`Ctrl+C` — シグナルハンドラで安全停止 (DB に `loop_health` 'stop' 記録)

### スケジュールタスク停止

```powershell
Stop-ScheduledTask -TaskName "SPECv2_PoC"
```

## 監視・確認

### DB 直接 SQL

```powershell
python -c "from src.spec_v2 import db; from pathlib import Path; r = db.daily_summary(Path('data/fx_spec_v2.db'), '2026-05-11'); import json; print(json.dumps(r, indent=2, default=str))"
```

期待出力:
```json
{
  "date": "2026-05-11",
  "regime_distribution": {"calm": 50, "transitional": 30, "volatile": 20},
  "pnl": {"n_closed": 3, "total_pips": 45.2, "total_jpy": 452.0},
  "n_open_trades": 0
}
```

### ログ確認

```powershell
Get-Content data/spec_v2_poc.log -Tail 50
Get-Content data/spec_v2_poc.log -Wait     # tail -f 相当
```

### MT5 ターミナルでポジション確認

GBP_JPY のオープンポジションが DB の `trades` (status='open') と一致しているか。

## トラブル時の対応

### M15 データ不足エラー
`M15 データ不足: ... 本 < 必要 5014 本`

→ MT5 ターミナルで GBP_JPY のヒストリーをダウンロードし直す。VPS で MT5 を起動して、Symbols ウィンドウから手動取得。

### MT5 connect 失敗
→ MT5 ターミナルが起動していない、または別プロセスで占有されている。VPS の MT5 ターミナルを再起動。

### 「ポジションが見つかりません」
→ DB と MT5 のポジション状態が不整合。一度ループ停止、MT5 ターミナルで手動でポジション確認・決済、DB の `trades` を `status='error'` に手動更新。

### 連続エラー
→ 連続でループが失敗している。`Get-Content data/spec_v2_poc.log -Tail 100` でエラー確認、必要なら停止して原因調査。

## 観察対象 (1-2 週間)

毎朝チェック:
1. **regime 分布**: VOLATILE / CALM / TRANSITIONAL の比率 (期待: VOLATILE 20-30%)
2. **エントリー件数**: VOLATILE 中の breakout 発生頻度 (1 日 0-3 件想定)
3. **PnL**: pips / JPY 累計
4. **異常**: error 件数、time_limit 決済の比率

## 撤退判断基準 (PoC 期間中)

karen レビュー指摘の「PoC 失敗時の物語破棄発火条件」を追加実装する想定:

- 30 日時点: 累計 PnL がデモ口座基準 -10% (= -100,000 JPY) → SeasonalDetector の前提見直し
- 60 日時点: ENTRY 件数 < 10 件 → ブレイクアウト雛形を見直し (§ 3-1 設計加速)
- 90 日時点: usable WFA fold が 3/5 を切る → SPEC v2 § 2-1 数値再検証

## 関連ファイル

- `src/spec_v2/poc_loop.py` (メインループ)
- `src/spec_v2/seasonal_detection.py` (確定版 SeasonalDetector)
- `src/spec_v2/signal_v2.py` (シグナル雛形)
- `src/spec_v2/data_fetcher.py` (M15+H1 取得)
- `src/spec_v2/db.py` (DB ヘルパー)
- `data/fx_spec_v2.db` (PoC 専用 DB)
- `data/spec_v2_poc.log` (PoC 専用ログ)
- `docs/vision/research/STEP_C_COMPLETION_2026-05-10.md` (Step C 完了総括)
