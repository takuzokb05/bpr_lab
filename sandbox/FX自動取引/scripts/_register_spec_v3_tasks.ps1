# SPEC v3 デモ運用タスクスケジューラ登録 (VPS で実行)
#
# - SPECv3_Demo:           60秒ループのメイン PoC (常駐)
# - SPECv3_AliveCheck:     1h ごと死活監視 (Once + RepetitionInterval=PT1H)
# - SPECv3_DailySummary:   JST 07:00 日次サマリ
#
# 重要: ExecutionTimeLimit を必ず PT0S (= 無制限) に指定
#       (feedback_task_scheduler_execution_time_limit.md の PT72H 罠回避)
#
# 旧 SPEC v2 タスクは Disabled 維持 (削除しない、人手で確認)

$py = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
$workDir = "C:\bpr_lab_spec_v2\sandbox\FX自動取引"  # VPS 上の clone パス

if (-not (Test-Path $py)) {
    Write-Error "Python が見つかりません: $py"
    exit 1
}
if (-not (Test-Path $workDir)) {
    Write-Error "作業ディレクトリが見つかりません: $workDir"
    exit 1
}

# 旧 SPEC v2 PoC タスクが動いていたら停止 (新旧並走防止)
foreach ($oldTask in @("SPECv2_PoC", "SPECv2_AliveCheck", "SPECv2_DailySummary")) {
    $task = Get-ScheduledTask -TaskName $oldTask -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "旧タスク $oldTask を停止 + 無効化"
        Stop-ScheduledTask -TaskName $oldTask -ErrorAction SilentlyContinue
        Disable-ScheduledTask -TaskName $oldTask -ErrorAction SilentlyContinue
    }
}

# ============================================================
# SPECv3_Demo (メインループ)
# ============================================================
Unregister-ScheduledTask -TaskName "SPECv3_Demo" -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction `
    -Execute $py `
    -Argument "-m src.spec_v3.demo_loop" `
    -WorkingDirectory $workDir

# AtStartup で常駐、StartBoundary 不要
$trigger = New-ScheduledTaskTrigger -AtStartup

$principal = New-ScheduledTaskPrincipal `
    -UserId "Administrator" `
    -LogonType S4U `
    -RunLevel Highest

# 重要: ExecutionTimeLimit=PT0S で無制限化 (PT72H 罠回避)
# MultipleInstances=IgnoreNew で再起動時の重複起動を防ぐ
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName "SPECv3_Demo" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "SPEC v3 Demo loop (Proposal 3): USD_JPY+GBP_JPY, LLM filter, lot 0.01"

Write-Host "=== SPECv3_Demo registered ==="

# ============================================================
# SPECv3_AliveCheck (死活、1h ごと)
# ============================================================
Unregister-ScheduledTask -TaskName "SPECv3_AliveCheck" -Confirm:$false -ErrorAction SilentlyContinue

$action2 = New-ScheduledTaskAction `
    -Execute $py `
    -Argument "scripts\spec_v3_alive_slack.py --quiet-when-alive" `
    -WorkingDirectory $workDir

# Once + RepetitionInterval (memory 確立済の最も確実な周期トリガー)
$tStart = New-ScheduledTaskTrigger -AtStartup
$tRepeat = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(5) `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration ([TimeSpan]::FromDays(3650))

$settings2 = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName "SPECv3_AliveCheck" `
    -Action $action2 `
    -Trigger @($tStart, $tRepeat) `
    -Principal $principal `
    -Settings $settings2 `
    -Description "SPEC v3 alive check (1h)"

Write-Host "=== SPECv3_AliveCheck registered ==="

# ============================================================
# SPECv3_DailySummary (JST 07:00)
# ============================================================
Unregister-ScheduledTask -TaskName "SPECv3_DailySummary" -Confirm:$false -ErrorAction SilentlyContinue

$action3 = New-ScheduledTaskAction `
    -Execute $py `
    -Argument "scripts\spec_v3_daily_summary_slack.py" `
    -WorkingDirectory $workDir

$tDaily = New-ScheduledTaskTrigger -Daily -At "07:00:00"

$settings3 = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName "SPECv3_DailySummary" `
    -Action $action3 `
    -Trigger $tDaily `
    -Principal $principal `
    -Settings $settings3 `
    -Description "SPEC v3 daily summary at JST 07:00"

Write-Host "=== SPECv3_DailySummary registered ==="

# ============================================================
# 確認出力
# ============================================================
$tasks = @("SPECv3_Demo", "SPECv3_AliveCheck", "SPECv3_DailySummary")
foreach ($tn in $tasks) {
    $task = Get-ScheduledTask -TaskName $tn
    Write-Host ("--- " + $tn + " ---")
    Write-Host ("  State: " + $task.State)
    Write-Host ("  ExecutionTimeLimit: " + $task.Settings.ExecutionTimeLimit)
    foreach ($t in $task.Triggers) {
        $line = "  Trigger: " + $t.GetType().Name + " StartBoundary=" + $t.StartBoundary
        if ($t.Repetition.Interval) { $line += " RepetitionInterval=" + $t.Repetition.Interval }
        if ($t.DaysInterval)        { $line += " DaysInterval=" + $t.DaysInterval }
        Write-Host $line
    }
}

# 旧タスクの状態確認 (Disabled になっているか)
Write-Host ""
Write-Host "=== 旧 SPEC v2 タスク状態 ==="
foreach ($old in @("SPECv2_PoC", "SPECv2_AliveCheck", "SPECv2_DailySummary")) {
    $t = Get-ScheduledTask -TaskName $old -ErrorAction SilentlyContinue
    if ($t) {
        Write-Host ("  " + $old + ": " + $t.State)
    } else {
        Write-Host ("  " + $old + ": (not registered)")
    }
}

Write-Host ""
Write-Host ("VPS local time: " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))
Write-Host "登録完了。SPECv3_Demo は VPS 再起動後に自動起動。"
Write-Host "手動起動する場合: Start-ScheduledTask -TaskName SPECv3_Demo"
