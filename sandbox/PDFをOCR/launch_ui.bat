@echo off
echo ======================================================================
echo   Gemini OCR Studio - Web UI Launcher
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
echo Starting Gemini OCR Studio Web UI...
echo.
echo The UI will open in your default browser at http://localhost:7860
echo Press Ctrl+C to stop the server
echo.

python ocr_ui.py

pause
