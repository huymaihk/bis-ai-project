@echo off
chcp 65001 >nul
echo ===================================================
echo   DONG BO CODE LEN GITHUB & STREAMLIT CLOUD (24/7)
echo ===================================================

cd /d "G:\My Drive\BIS_AI_PROJECT"

echo 1. Kiem tra thay doi...
git status --short

echo 2. Gom tat ca thay doi moi...
git add .

set /p msg="Nhap ghi chu thay doi (Enter de dung mac dinh: 'Cap nhat tu Antigravity'): "
if "%msg%"=="" set msg=Cap nhat tu Antigravity AI

echo 3. Luu thay doi (Commit)...
git commit -m "%msg%"

echo 4. Day len GitHub (Push)...
git push origin main

echo ===================================================
echo   THANH CONG! Streamlit Cloud se tu dong cap nhat
echo   sau 5-10 giay ma khong can thao tac gi them!
echo ===================================================
pause

