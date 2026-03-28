@echo off
REM ============================================================
REM FX自動取引システム 停止スクリプト
REM main.py プロセスを安全に停止する
REM ============================================================

echo main.py プロセスを検索中...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| find "PID"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>NUL | find "main.py" >NUL
    if not errorlevel 1 (
        echo PID %%i の main.py を停止します...
        taskkill /PID %%i /F
    )
)

echo 完了。
pause
