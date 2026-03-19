@echo off
cd /d C:\Users\Administrator\Desktop\github

:: Step 1: Commit the rename changes
git add -A
git commit -m "Rename project to github-cli"

:: Step 2: Create new GitHub repo
set HTTPS_PROXY=http://127.0.0.1:7890
set HTTP_PROXY=http://127.0.0.1:7890
gh repo create BranchCrypto/github-cli --public --description "A production-ready, visual, interactive GitHub client that runs entirely in your terminal."

:: Step 3: Update remote and push
git remote set-url origin https://github.com/BranchCrypto/github-cli.git
git push -u origin main --force

echo.
echo === DONE ===
