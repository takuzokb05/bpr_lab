# SPEC v2 PoC 観察基盤タスク登録スクリプト (VPS で実行)
# - SPECv2_AliveCheck: 1h ごと、警告時のみ Slack
# - SPECv2_DailySummary: JST 07:00 daily Slack

$py = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
$workDir = "C:\bpr_lab_spec_v2\sandbox\FX自動取引"

# ============================================
# SPECv2_AliveCheck
# ============================================
Unregister-ScheduledTask -TaskName "SPECv2_AliveCheck" -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute $py -Argument "scripts\poc_alive_slack.py --quiet-when-alive" -WorkingDirectory $workDir

$tStart = New-ScheduledTaskTrigger -AtStartup
$tRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::FromDays(3650))

$principal = New-ScheduledTaskPrincipal -UserId "Administrator" -LogonType S4U -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "SPECv2_AliveCheck" -Action $action -Trigger @($tStart, $tRepeat) -Principal $principal -Settings $settings -Description "SPEC v2 PoC alive check: 1h interval"

Write-Host "=== SPECv2_AliveCheck registered ==="

# ============================================
# SPECv2_DailySummary
# ============================================
Unregister-ScheduledTask -TaskName "SPECv2_DailySummary" -Confirm:$false -ErrorAction SilentlyContinue

$action2 = New-ScheduledTaskAction -Execute $py -Argument "scripts\poc_daily_summary_slack.py" -WorkingDirectory $workDir
$tDaily = New-ScheduledTaskTrigger -Daily -At "07:00:00"
$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "SPECv2_DailySummary" -Action $action2 -Trigger $tDaily -Principal $principal -Settings $settings2 -Description "SPEC v2 PoC daily summary: JST 07:00"

Write-Host "=== SPECv2_DailySummary registered ==="

# 確認出力
$tasks = @("SPECv2_AliveCheck", "SPECv2_DailySummary")
foreach ($tn in $tasks) {
    $task = Get-ScheduledTask -TaskName $tn
    Write-Host ("--- " + $tn + " ---")
    Write-Host ("  State: " + $task.State)
    Write-Host ("  ExecutionTimeLimit: " + $task.Settings.ExecutionTimeLimit)
    foreach ($t in $task.Triggers) {
        $line = "  Trigger: " + $t.GetType().Name + " StartBoundary=" + $t.StartBoundary
        if ($t.Repetition.Interval) { $line += " RepetitionInterval=" + $t.Repetition.Interval }
        if ($t.DaysInterval) { $line += " DaysInterval=" + $t.DaysInterval }
        Write-Host $line
    }
}

Write-Host ("VPS local time: " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))
