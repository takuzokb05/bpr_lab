# ============================================================
# FX自動取引システム — VPS自動セットアップスクリプト
#
# 使い方:
#   1. RDPでVPSに接続
#   2. fx_auto_trading_deploy.zip と vps_setup.ps1 をデスクトップにコピー
#   3. PowerShellを管理者として開く
#   4. Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   5. cd Desktop
#   6. .\vps_setup.ps1
# ============================================================

$ErrorActionPreference = "Stop"

# --- 設定 ---
$PROJECT_DIR = "C:\Users\Administrator\FX_AutoTrading"
$PYTHON_VERSION = "3.11.9"
$PYTHON_URL = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-amd64.exe"
$MT5_URL = "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
$DEPLOY_ZIP = "$PSScriptRoot\fx_auto_trading_deploy.zip"

function Write-Step {
    param([string]$Step, [string]$Message)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $Step : $Message" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-OK {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "  [WARN] $Message" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

# ============================================================
# Step 0: 前提チェック
# ============================================================
Write-Step "Step 0" "前提チェック"

# 管理者権限チェック
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Err "管理者として実行してください（PowerShellを右クリック→管理者として実行）"
    exit 1
}
Write-OK "管理者権限: 確認"

# ZIPファイル確認
if (-not (Test-Path $DEPLOY_ZIP)) {
    # デスクトップも探す
    $altPath = "$env:USERPROFILE\Desktop\fx_auto_trading_deploy.zip"
    if (Test-Path $altPath) {
        $DEPLOY_ZIP = $altPath
    } else {
        Write-Err "デプロイ用ZIPが見つかりません: $DEPLOY_ZIP"
        Write-Err "fx_auto_trading_deploy.zip をこのスクリプトと同じフォルダに置いてください"
        exit 1
    }
}
Write-OK "ZIPファイル: $DEPLOY_ZIP"

# ============================================================
# Step 1: Pythonインストール
# ============================================================
Write-Step "Step 1" "Pythonインストール"

$pythonInstalled = $false
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "Python 3\.\d+") {
        Write-OK "Python はインストール済み: $pyVersion"
        $pythonInstalled = $true
    }
} catch {
    # Pythonが見つからない
}

if (-not $pythonInstalled) {
    Write-Host "  Python $PYTHON_VERSION をダウンロード中..."
    $installerPath = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri $PYTHON_URL -OutFile $installerPath -UseBasicParsing
    Write-OK "ダウンロード完了"

    Write-Host "  インストール中（サイレントモード）..."
    Start-Process -Wait -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"

    # PATHを更新
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    try {
        $pyVersion = python --version 2>&1
        Write-OK "インストール完了: $pyVersion"
    } catch {
        Write-Err "Pythonインストール後にpythonコマンドが見つかりません"
        Write-Err "手動でインストールし、PATHに追加してからやり直してください"
        exit 1
    }
}

# pipの確認
try {
    $pipVersion = pip --version 2>&1
    Write-OK "pip: $pipVersion"
} catch {
    Write-Warn "pipが見つかりません。python -m ensurepip を実行します"
    python -m ensurepip
}

# ============================================================
# Step 2: プロジェクト展開
# ============================================================
Write-Step "Step 2" "プロジェクト展開"

if (Test-Path $PROJECT_DIR) {
    Write-Warn "既存のプロジェクトディレクトリが見つかりました: $PROJECT_DIR"
    $confirm = Read-Host "  上書きしますか？ (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "  スキップしました"
    } else {
        Remove-Item -Recurse -Force $PROJECT_DIR
        Write-OK "既存ディレクトリを削除"
    }
}

if (-not (Test-Path $PROJECT_DIR)) {
    Write-Host "  ZIPを展開中..."
    Expand-Archive -Path $DEPLOY_ZIP -DestinationPath $PROJECT_DIR -Force
    Write-OK "展開完了: $PROJECT_DIR"
}

# data ディレクトリ作成（ログ・DB用）
$dataDir = "$PROJECT_DIR\data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
    Write-OK "data ディレクトリ作成"
}

# ============================================================
# Step 3: Python仮想環境 + パッケージインストール
# ============================================================
Write-Step "Step 3" "仮想環境構築・パッケージインストール"

$venvDir = "$PROJECT_DIR\venv"

if (-not (Test-Path "$venvDir\Scripts\python.exe")) {
    Write-Host "  仮想環境を作成中..."
    python -m venv $venvDir
    Write-OK "仮想環境作成完了"
} else {
    Write-OK "仮想環境は既に存在"
}

# 仮想環境のpipでインストール
Write-Host "  パッケージインストール中（少し時間がかかります）..."
& "$venvDir\Scripts\pip.exe" install --upgrade pip 2>&1 | Out-Null
& "$venvDir\Scripts\pip.exe" install -r "$PROJECT_DIR\requirements.txt" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-OK "全パッケージのインストール完了"
} else {
    Write-Err "パッケージインストールでエラーが発生しました"
    Write-Host "  手動で確認してください: cd $PROJECT_DIR && venv\Scripts\pip install -r requirements.txt"
}

# ============================================================
# Step 4: .envファイル作成
# ============================================================
Write-Step "Step 4" ".envファイル作成"

$envPath = "$PROJECT_DIR\.env"

if (Test-Path $envPath) {
    Write-OK ".envファイルは既に存在"
    $overwriteEnv = Read-Host "  上書きしますか？ (y/N)"
    if ($overwriteEnv -ne "y" -and $overwriteEnv -ne "Y") {
        Write-Host "  スキップしました"
    } else {
        Remove-Item $envPath
    }
}

if (-not (Test-Path $envPath)) {
    Write-Host ""
    Write-Host "  Telegram Bot の認証情報を入力してください" -ForegroundColor Yellow
    Write-Host "  （ローカルPCの .env ファイルに記載されている値です）" -ForegroundColor Yellow
    Write-Host ""
    $telegramToken = Read-Host "  TELEGRAM_BOT_TOKEN"
    $telegramChatId = Read-Host "  TELEGRAM_CHAT_ID"

    $envContent = @"
# OANDA API設定（MT5使用のため不要）
OANDA_API_KEY=
OANDA_ACCOUNT_ID=
OANDA_ENVIRONMENT=practice

# Telegram Bot設定
TELEGRAM_BOT_TOKEN=$telegramToken
TELEGRAM_CHAT_ID=$telegramChatId
"@

    Set-Content -Path $envPath -Value $envContent -Encoding UTF8
    Write-OK ".envファイル作成完了"
}

# ============================================================
# Step 5: MetaTrader 5 インストール
# ============================================================
Write-Step "Step 5" "MetaTrader 5"

$mt5Running = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
if ($mt5Running) {
    Write-OK "MT5は既に起動中"
} else {
    # MT5がインストールされているか確認
    $mt5Path = "C:\Program Files\MetaTrader 5\terminal64.exe"
    $mt5AltPaths = @(
        "C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        "$env:APPDATA\..\Local\Programs\MetaTrader 5\terminal64.exe",
        "C:\MetaTrader 5\terminal64.exe"
    )

    $mt5Found = $false
    if (Test-Path $mt5Path) {
        $mt5Found = $true
    } else {
        foreach ($p in $mt5AltPaths) {
            if (Test-Path $p) {
                $mt5Path = $p
                $mt5Found = $true
                break
            }
        }
    }

    if ($mt5Found) {
        Write-OK "MT5はインストール済み: $mt5Path"
        Write-Host "  MT5を起動します..."
        Start-Process $mt5Path
        Write-Host "  MT5が起動したら、外為ファイネストのデモ口座にログインしてください" -ForegroundColor Yellow
        Write-Host "    サーバー: GaitameFinest-Demo" -ForegroundColor Yellow
        Write-Host "    口座番号: 22005467" -ForegroundColor Yellow
    } else {
        Write-Warn "MT5がインストールされていません"
        $installMT5 = Read-Host "  MT5インストーラをダウンロードしますか？ (Y/n)"
        if ($installMT5 -ne "n" -and $installMT5 -ne "N") {
            $mt5Installer = "$env:TEMP\mt5setup.exe"
            Write-Host "  ダウンロード中..."
            Invoke-WebRequest -Uri $MT5_URL -OutFile $mt5Installer -UseBasicParsing
            Write-OK "ダウンロード完了"
            Write-Host "  インストーラを起動します（手動でインストールしてください）..."
            Start-Process $mt5Installer
            Write-Host ""
            Write-Host "  MT5インストール後の操作:" -ForegroundColor Yellow
            Write-Host "    1. MT5を起動" -ForegroundColor Yellow
            Write-Host "    2. ファイル → デモ口座の開設 → GaitameFinest-Demo" -ForegroundColor Yellow
            Write-Host "    3. 既存口座 → 口座番号: 22005467 を入力" -ForegroundColor Yellow
            Write-Host ""
            Read-Host "  MT5のセットアップが完了したらEnterを押してください"
        }
    }
}

# ============================================================
# Step 6: SSH修復（オプション）
# ============================================================
Write-Step "Step 6" "SSH設定（リモート管理用）"

$sshdService = Get-Service -Name sshd -ErrorAction SilentlyContinue
if ($sshdService) {
    if ($sshdService.Status -eq "Running") {
        Write-OK "OpenSSH Server: 起動中"
    } else {
        Write-Host "  OpenSSH Serverを起動します..."
        Start-Service sshd
        Set-Service -Name sshd -StartupType Automatic
        Write-OK "OpenSSH Server: 起動＋自動起動設定完了"
    }
} else {
    Write-Host "  OpenSSH Serverをインストールします..."
    try {
        Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
        Start-Service sshd
        Set-Service -Name sshd -StartupType Automatic
        Write-OK "OpenSSH Server: インストール＋起動完了"
    } catch {
        Write-Warn "OpenSSH Serverのインストールに失敗: $_"
        Write-Warn "リモート管理はRDPのみになります"
    }
}

# ファイアウォールルール確認
$fwRule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if (-not $fwRule) {
    Write-Host "  ファイアウォールルールを追加..."
    New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" `
        -DisplayName "OpenSSH Server (sshd)" `
        -Enabled True -Direction Inbound -Protocol TCP `
        -Action Allow -LocalPort 22 | Out-Null
    Write-OK "ファイアウォール: ポート22許可"
} else {
    Write-OK "ファイアウォール: ルール確認済み"
}

# SSHのリスニング確認
$sshListening = netstat -an | Select-String ":22 " | Select-String "LISTENING"
if ($sshListening) {
    Write-OK "SSH: ポート22でリスニング中"
} else {
    Write-Warn "SSH: ポート22でリスニングしていません。サービスを確認してください"
}

# ============================================================
# Step 7: 動作確認（ドライラン）
# ============================================================
Write-Step "Step 7" "動作確認（ドライラン）"

# MT5が起動しているか確認
$mt5Running = Get-Process -Name "terminal64" -ErrorAction SilentlyContinue
if (-not $mt5Running) {
    Write-Warn "MT5が起動していません。ドライランにはMT5が必要です"
    Write-Host "  MT5を起動してデモ口座にログイン後、以下のコマンドで手動実行してください:" -ForegroundColor Yellow
    Write-Host "    cd $PROJECT_DIR" -ForegroundColor Yellow
    Write-Host "    venv\Scripts\activate" -ForegroundColor Yellow
    Write-Host "    python main.py --dry-run" -ForegroundColor Yellow
} else {
    Write-Host "  ドライラン実行中..."
    Push-Location $PROJECT_DIR
    & "$venvDir\Scripts\python.exe" main.py --dry-run
    $dryRunResult = $LASTEXITCODE
    Pop-Location

    if ($dryRunResult -eq 0) {
        Write-OK "ドライラン成功！"
    } else {
        Write-Err "ドライランでエラーが発生しました（exit code: $dryRunResult）"
        Write-Host "  ログを確認: type $PROJECT_DIR\data\trading.log" -ForegroundColor Yellow
    }
}

# ============================================================
# Step 8: 自動起動設定
# ============================================================
Write-Step "Step 8" "自動起動設定"

# start_trading.bat のパスをVPS用に更新
$batPath = "$PROJECT_DIR\scripts\start_trading.bat"
if (Test-Path $batPath) {
    # PROJECT_DIRが正しいか確認（batファイル内のパスをVPS用に合わせる）
    $batContent = Get-Content $batPath -Raw
    if ($batContent -notmatch [regex]::Escape($PROJECT_DIR)) {
        Write-Host "  start_trading.bat のプロジェクトパスを更新中..."
        $batContent = $batContent -replace "C:\\Users\\Administrator\\FX自動取引", $PROJECT_DIR
        Set-Content -Path $batPath -Value $batContent -Encoding ASCII
        Write-OK "start_trading.bat パス更新完了"
    }
}

# タスクスケジューラに登録
$taskName = "FX_AutoTrading"
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-OK "タスクスケジューラ: '$taskName' は登録済み"
    $updateTask = Read-Host "  再登録しますか？ (y/N)"
    if ($updateTask -eq "y" -or $updateTask -eq "Y") {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        $existingTask = $null
    }
}

if (-not $existingTask) {
    Write-Host "  タスクスケジューラに登録中..."
    $action = New-ScheduledTaskAction `
        -Execute $batPath `
        -WorkingDirectory $PROJECT_DIR
    $trigger = New-ScheduledTaskTrigger -AtStartup
    # 30秒遅延を設定
    $trigger.Delay = "PT30S"
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 1)
    $principal = New-ScheduledTaskPrincipal `
        -UserId "SYSTEM" `
        -LogonType ServiceAccount `
        -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal | Out-Null

    Write-OK "タスクスケジューラ: '$taskName' 登録完了（スタートアップ時に自動実行）"
}

# MT5のスタートアップ登録
$startupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$mt5Shortcut = "$startupFolder\MetaTrader 5.lnk"

if (-not (Test-Path $mt5Shortcut)) {
    # MT5のパスを検索
    $mt5Exe = $null
    $searchPaths = @(
        "C:\Program Files\MetaTrader 5\terminal64.exe",
        "C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
    )
    foreach ($p in $searchPaths) {
        if (Test-Path $p) { $mt5Exe = $p; break }
    }

    if ($mt5Exe) {
        $WshShell = New-Object -ComObject WScript.Shell
        $shortcut = $WshShell.CreateShortcut($mt5Shortcut)
        $shortcut.TargetPath = $mt5Exe
        $shortcut.WorkingDirectory = Split-Path $mt5Exe
        $shortcut.Save()
        Write-OK "MT5: スタートアップに登録完了"
    } else {
        Write-Warn "MT5の実行ファイルが見つかりません。手動でスタートアップに登録してください"
    }
} else {
    Write-OK "MT5: スタートアップ登録済み"
}

# ============================================================
# 完了サマリー
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  セットアップ完了！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  プロジェクト: $PROJECT_DIR"
Write-Host "  仮想環境:     $venvDir"
Write-Host "  設定ファイル: $envPath"
Write-Host ""
Write-Host "  --- 次のステップ ---" -ForegroundColor Yellow
Write-Host "  1. MT5でデモ口座にログイン済みか確認"
Write-Host "  2. ドライランテスト:" -ForegroundColor Yellow
Write-Host "       cd $PROJECT_DIR"
Write-Host "       venv\Scripts\activate"
Write-Host "       python main.py --dry-run"
Write-Host ""
Write-Host "  3. 本番ペーパートレード開始:" -ForegroundColor Yellow
Write-Host "       python main.py"
Write-Host ""
Write-Host "  4. Telegramコマンド:" -ForegroundColor Yellow
Write-Host "       /status     - ステータス確認"
Write-Host "       /positions  - ポジション一覧"
Write-Host "       /balance    - 残高確認"
Write-Host "       /stop       - 緊急停止"
Write-Host "       /start      - 再開"
Write-Host ""
Write-Host "  VPS再起動時: MT5 + main.py が自動起動します"
Write-Host ""
