@echo off
echo PATH=%PATH% > debug_info.txt
where node >> debug_info.txt 2>&1
node -v >> debug_info.txt 2>&1
echo DONE >> debug_info.txt
