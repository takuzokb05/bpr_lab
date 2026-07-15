@echo off
echo ======================================================================
echo   Gemini OCR Studio - Server Launcher
echo ======================================================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Installing websockets if needed...
pip install websockets --quiet

echo.
echo Starting WebSocket Server...
echo.
echo Server will start on ws://localhost:8765
echo Open ocr_ui.html in your browser to access the UI
echo.
echo Press Ctrl+C to stop the server
echo.

python ocr_server.py

pause
