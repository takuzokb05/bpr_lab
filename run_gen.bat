@echo off
set GEMINI_API_KEY=AIzaSyC6Z8PHJe_fpuwf4HysOtyLRdTWaOTfD1k
where node
node data/generate-image.js "cute cat illustration" "images/cat.png" > gen_output.txt 2>&1
echo EXIT_CODE=%ERRORLEVEL% >> gen_output.txt
