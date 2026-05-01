$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\bpr_lab\fx_trading\scripts\memory_monitor.ps1'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'FX_MemoryMonitor' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'python/MT5/OS memory monitor, 1-min interval' -Force | Out-Null
Get-ScheduledTask -TaskName 'FX_MemoryMonitor' | Format-List TaskName,State
