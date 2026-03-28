# デプロイ用ZIPアーカイブ作成スクリプト
$src = Split-Path -Parent $PSScriptRoot
$dst = Join-Path $src "deploy\fx_auto_trading_deploy.zip"
$tmp = Join-Path $src "deploy\_staging"

Write-Host "デプロイパッケージを作成します..."
Write-Host "ソース: $src"

# 一時ディレクトリにコピー
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
New-Item -ItemType Directory -Path $tmp | Out-Null

$exclude = @('.env', '.git', '.claude', 'venv', 'data', 'deploy', '__pycache__')
Get-ChildItem -Path $src -Exclude $exclude | Copy-Item -Destination $tmp -Recurse -Force

# __pycache__ を再帰的に削除
Get-ChildItem -Path $tmp -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

# ZIP作成
$deployDir = Join-Path $src "deploy"
if (-not (Test-Path $deployDir)) { New-Item -ItemType Directory -Path $deployDir | Out-Null }
if (Test-Path $dst) { Remove-Item $dst }
Compress-Archive -Path "$tmp\*" -DestinationPath $dst -CompressionLevel Optimal

# 一時ディレクトリ削除
Remove-Item -Recurse -Force $tmp

$sizeKB = [math]::Round((Get-Item $dst).Length / 1KB, 1)
Write-Host ""
Write-Host "完了: $dst ($sizeKB KB)" -ForegroundColor Green
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor Yellow
Write-Host '  1. RDPでVPSに接続'
Write-Host "  2. $dst をVPSのデスクトップにコピー"
Write-Host '  3. scripts\vps_setup.ps1 もVPSのデスクトップにコピー'
Write-Host '  4. VPS上で管理者PowerShellを開いて実行:'
Write-Host '       cd C:\Users\Administrator\Desktop'
Write-Host '       Set-ExecutionPolicy RemoteSigned -Scope CurrentUser'
Write-Host '       .\vps_setup.ps1'
