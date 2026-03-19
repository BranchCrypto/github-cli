@echo off
cd /d C:\Users\Administrator\Desktop\github
git add -A
git commit --allow-empty -m "Remove temp files"
set HTTPS_PROXY=http://127.0.0.1:7890
set HTTP_PROXY=http://127.0.0.1:7890
git push
echo === DONE ===
