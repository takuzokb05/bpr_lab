@echo off
REM ============================================================
REM FX自動取引システム 起動スクリプト
REM VPSのタスクスケジューラから自動実行される
REM ============================================================

setlocal

REM --- 設定 ---
set PROJECT_DIR=C:\Users\Administrator\FX自動取引
set VENV_DIR=%PROJECT_DIR%\venv
set MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
set LOG_FILE=%PROJECT_DIR%\data\startup.log

REM --- ログ出力開始 ---
echo [%date% %time%] === 起動スクリプト開始 === >> "%LOG_FILE%"

REM --- MT5が起動していなければ起動 ---
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I "terminal64.exe" >NUL
if errorlevel 1 (
    echo [%date% %time%] MT5を起動します >> "%LOG_FILE%"
    start "" "%MT5_PATH%"
    REM MT5の初期化を待つ
    timeout /t 15 /nobreak >NUL
) else (
    echo [%date% %time%] MT5は既に起動中 >> "%LOG_FILE%"
)

REM --- 仮想環境をアクティベート ---
if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
    echo [%date% %time%] 仮想環境をアクティベート >> "%LOG_FILE%"
) else (
    echo [%date% %time%] 警告: 仮想環境が見つかりません >> "%LOG_FILE%"
)

REM --- プロジェクトディレクトリに移動 ---
cd /d "%PROJECT_DIR%"

REM --- main.py 実行 ---
echo [%date% %time%] main.py を起動します >> "%LOG_FILE%"
python main.py >> "%LOG_FILE%" 2>&1

echo [%date% %time%] main.py が終了しました（exit code: %errorlevel%） >> "%LOG_FILE%"

endlocal
