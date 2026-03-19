@echo off
cd /d C:\Users\Administrator\Desktop\github
del _clean.bat
git add -A
git commit -m "Clean up"
set HTTPS_PROXY=http://127.0.0.1:7890
set HTTP_PROXY=http://127.0.0.1:7890
git push
echo === DONE ===
