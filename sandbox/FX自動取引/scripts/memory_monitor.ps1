$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$os = Get-CimInstance Win32_OperatingSystem
$freeMB = [int]($os.FreePhysicalMemory / 1KB)
$totalMB = [int]($os.TotalVisibleMemorySize / 1KB)
$usedPct = [int](100 - ($freeMB * 100 / $totalMB))
$py = Get-Process python -ErrorAction SilentlyContinue | Sort-Object StartTime | Select-Object -First 1
$term = Get-Process terminal64 -ErrorAction SilentlyContinue | Select-Object -First 1
$termAlive = if ($term) { 1 } else { 0 }
if ($py) {
    $wsMB = [int]($py.WS / 1MB)
    $pmMB = [int]($py.PM / 1MB)
    $pyPid = $py.Id
    $ageMin = [int](((Get-Date) - $py.StartTime).TotalMinutes)
    $line = "$ts py_pid=$pyPid py_age_min=$ageMin py_ws_mb=$wsMB py_pm_mb=$pmMB os_free_mb=$freeMB os_used_pct=$usedPct term_alive=$termAlive"
} else {
    $line = "$ts py_pid=NONE os_free_mb=$freeMB os_used_pct=$usedPct term_alive=$termAlive"
}
Add-Content -Path 'C:\bpr_lab\sandbox\FX自動取引\data\memory_monitor.log' -Value $line -Encoding UTF8
