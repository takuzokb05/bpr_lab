@echo off
set "PATH=C:\Program Files\nodejs;%PATH%"
echo Starting Ganbaru List Server...
npm run dev -- --host
pause
