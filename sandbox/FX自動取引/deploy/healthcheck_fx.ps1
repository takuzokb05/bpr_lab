<#
.SYNOPSIS
    FX自動取引システム ヘルスチェック (Windows VPS 用)

.DESCRIPTION
    以下4項目を監視し、異常時に Slack #ai-alerts へ通知する。
      1. main.py プロセス生存 (python で main.py を実行中か)
      2. trading.log の更新時刻 (10分以上更新なしで異常)
      3. FX_MarketAnalysis タスクの LastTaskResult (0以外で異常)
      4. MT5 terminal64.exe プロセス生存
    main.py が死んでいれば Start-Process で自動再起動する。
    タスクスケジューラで10分毎に実行される想定。
#>

# ─────────────────────────────────────────
# 設定
# ─────────────────────────────────────────
$FxRoot          = 'C:\bpr_lab\fx_trading'
$TradingLogPath  = Join-Path $FxRoot 'data\trading.log'
$HealthLogPath   = Join-Path $FxRoot 'data\healthcheck.log'
$EnvFilePath     = Join-Path $FxRoot '.env'
$PythonExe       = 'C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe'
$MainScript      = 'main.py'
$StdoutLog       = 'data\stdout.log'
$StderrLog       = 'data\stderr.log'
$LogStaleMinutes = 10
$TaskName        = 'FX_MarketAnalysis'

# ─────────────────────────────────────────
# ログ関数 (コンソール出力は抑制、ファイルのみ)
# ─────────────────────────────────────────
function Write-HealthLog {
    param(
        [string]$Level,
        [string]$Message
    )
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$timestamp] [$Level] $Message"
    try {
        Add-Content -Path $HealthLogPath -Value $line -Encoding UTF8
    } catch {
        # ログ書き込み失敗は握りつぶす (他の処理は継続)
    }
}

# ─────────────────────────────────────────
# .env から Webhook URL を取得
# ─────────────────────────────────────────
function Get-WebhookUrl {
    if (-not (Test-Path $EnvFilePath)) {
        return $null
    }
    try {
        $line = Select-String -Path $EnvFilePath -Pattern '^SLACK_ALERTS_WEBHOOK_URL=' -ErrorAction Stop | Select-Object -First 1
        if ($line) {
            $value = $line.Line -replace '^SLACK_ALERTS_WEBHOOK_URL=', ''
            $value = $value.Trim().Trim('"').Trim("'")
            if ($value) { return $value }
        }
    } catch {
        Write-HealthLog 'ERROR' ".env 読み込み失敗: $($_.Exception.Message)"
    }
    return $null
}

# ─────────────────────────────────────────
# Slack 通知
# ─────────────────────────────────────────
function Send-SlackAlert {
    param([string]$Text)
    $url = Get-WebhookUrl
    if (-not $url) {
        Write-HealthLog 'WARN' 'Webhook URL が取得できないため Slack 通知をスキップ'
        return
    }
    try {
        $payload = @{ text = $Text } | ConvertTo-Json -Compress
        $null = Invoke-RestMethod -Uri $url -Method Post -Body $payload -ContentType 'application/json' -TimeoutSec 15
        Write-HealthLog 'INFO' 'Slack 通知送信成功'
    } catch {
        Write-HealthLog 'ERROR' "Slack 通知送信失敗: $($_.Exception.Message)"
    }
}

# ─────────────────────────────────────────
# 監視1: main.py プロセス生存確認
# ─────────────────────────────────────────
function Test-MainPyAlive {
    try {
        # CommandLine に main.py を含む python プロセスを検索
        $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction Stop |
                 Where-Object { $_.CommandLine -and $_.CommandLine -match 'main\.py' }
        return [bool]$procs
    } catch {
        Write-HealthLog 'ERROR' "main.py プロセス確認失敗: $($_.Exception.Message)"
        return $false
    }
}

# ─────────────────────────────────────────
# main.py 自動再起動
# ssh セッション経由の Start-Process は親切断時に子プロセスも巻き添え
# で死ぬため、必ず Start-ScheduledTask 経由で SYSTEM セッション起動する。
# ─────────────────────────────────────────
function Restart-MainPy {
    try {
        Start-ScheduledTask -TaskName 'FX_AutoTrading' -ErrorAction Stop
        Write-HealthLog 'INFO' 'FX_AutoTrading タスクを起動（Start-ScheduledTask）'
        return $true
    } catch {
        Write-HealthLog 'ERROR' "main.py 再起動失敗: $($_.Exception.Message)"
        return $false
    }
}

# ─────────────────────────────────────────
# 監視2: trading.log 更新時刻
# ─────────────────────────────────────────
function Test-TradingLogFresh {
    if (-not (Test-Path $TradingLogPath)) {
        Write-HealthLog 'ERROR' "trading.log が存在しない: $TradingLogPath"
        return @{ Ok = $false; Reason = 'trading.log が存在しない' }
    }
    try {
        $lastWrite = (Get-Item $TradingLogPath).LastWriteTime
        $minutesAgo = [math]::Round(((Get-Date) - $lastWrite).TotalMinutes, 1)
        if ($minutesAgo -gt $LogStaleMinutes) {
            return @{ Ok = $false; Reason = "trading.log が $minutesAgo 分前から更新なし (閾値 $LogStaleMinutes 分)" }
        }
        return @{ Ok = $true; Reason = "最終更新 $minutesAgo 分前" }
    } catch {
        Write-HealthLog 'ERROR' "trading.log 確認失敗: $($_.Exception.Message)"
        return @{ Ok = $false; Reason = "trading.log 確認失敗: $($_.Exception.Message)" }
    }
}

# ─────────────────────────────────────────
# 監視3: FX_MarketAnalysis タスクの前回結果
# ─────────────────────────────────────────
function Test-MarketAnalysisTask {
    try {
        $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction Stop
        # 0 = 成功, 267011 = まだ実行されていない (初期状態は許容)
        if ($info.LastTaskResult -eq 0 -or $info.LastTaskResult -eq 267011) {
            return @{ Ok = $true; Reason = "LastTaskResult=$($info.LastTaskResult)" }
        }
        return @{ Ok = $false; Reason = "FX_MarketAnalysis LastTaskResult=$($info.LastTaskResult) (LastRunTime=$($info.LastRunTime))" }
    } catch {
        Write-HealthLog 'ERROR' "FX_MarketAnalysis タスク確認失敗: $($_.Exception.Message)"
        return @{ Ok = $false; Reason = "タスク確認失敗: $($_.Exception.Message)" }
    }
}

# ─────────────────────────────────────────
# 監視4: MT5 terminal64.exe プロセス生存
# ─────────────────────────────────────────
function Test-MT5Alive {
    try {
        $mt5 = Get-Process -Name 'terminal64' -ErrorAction SilentlyContinue
        return [bool]$mt5
    } catch {
        Write-HealthLog 'ERROR' "MT5 プロセス確認失敗: $($_.Exception.Message)"
        return $false
    }
}

# ─────────────────────────────────────────
# メイン
# ─────────────────────────────────────────
Write-HealthLog 'INFO' '===== ヘルスチェック開始 ====='

$alerts = @()

# 1. main.py
if (Test-MainPyAlive) {
    Write-HealthLog 'OK' 'main.py プロセス生存'
} else {
    Write-HealthLog 'ALERT' 'main.py プロセスが存在しない → 再起動試行'
    $restarted = Restart-MainPy
    if ($restarted) {
        $alerts += ':rotating_light: main.py がダウン検出 → 自動再起動を試行しました (VPS 160.251.221.43)'
    } else {
        $alerts += ':rotating_light: main.py がダウン検出 → 自動再起動に失敗しました (VPS 160.251.221.43) 手動対応必要'
    }
}

# 2. trading.log
$logCheck = Test-TradingLogFresh
if ($logCheck.Ok) {
    Write-HealthLog 'OK' "trading.log 更新OK ($($logCheck.Reason))"
} else {
    Write-HealthLog 'ALERT' $logCheck.Reason
    $alerts += ":warning: trading.log ストール検出 — $($logCheck.Reason)"
}

# 3. FX_MarketAnalysis タスク
$taskCheck = Test-MarketAnalysisTask
if ($taskCheck.Ok) {
    Write-HealthLog 'OK' "FX_MarketAnalysis OK ($($taskCheck.Reason))"
} else {
    Write-HealthLog 'ALERT' $taskCheck.Reason
    $alerts += ":warning: FX_MarketAnalysis タスク失敗 — $($taskCheck.Reason)"
}

# 4. MT5
if (Test-MT5Alive) {
    Write-HealthLog 'OK' 'MT5 terminal64.exe 生存'
} else {
    Write-HealthLog 'ALERT' 'MT5 terminal64.exe が存在しない'
    $alerts += ':rotating_light: MT5 terminal64.exe ダウン検出 — MT5 ターミナル起動が必要 (VPS 160.251.221.43)'
}

# ─────────────────────────────────────────
# 異常があれば Slack 通知をまとめて送る
# ─────────────────────────────────────────
if ($alerts.Count -gt 0) {
    $header = "*[FX Healthcheck] 異常検知 ($($alerts.Count)件)* — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $body = $header + "`n" + ($alerts -join "`n")
    Send-SlackAlert -Text $body
}

Write-HealthLog 'INFO' "===== ヘルスチェック完了 (異常 $($alerts.Count)件) ====="
