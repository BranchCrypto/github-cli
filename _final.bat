@echo off
cd /d C:\Users\Administrator\Desktop\github
del _clean2.bat
git add -A
git commit --allow-empty -m "Final cleanup"
set HTTPS_PROXY=http://127.0.0.1:7890
set HTTP_PROXY=http://127.0.0.1:7890
git push
echo === DONE ===
