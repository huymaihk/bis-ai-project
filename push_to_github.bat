@echo off
title DONG BO GITHUB - BIS AI PROJECT
echo =====================================================================
echo   DONG BO MA NGUON LEN GITHUB: huymaihk/bis-ai-project (Nhanh main)
echo =====================================================================
echo.
cd /d "C:\Users\Dell\bis-ai-project"

echo Dang kiem tra trang thai Git...
"C:\Users\Dell\AppData\Local\MinGit\cmd\git.exe" status

echo.
echo Dang day commit "Add LEGO AI Team HQ UI and Auth (adminhuy)" len GitHub...
"C:\Users\Dell\AppData\Local\MinGit\cmd\git.exe" push origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo =====================================================================
    echo   [SUCCESS] DA DONG BO THANH CONG LEN GITHUB!
    echo   Streamlit Cloud se tu dong cap nhat giao dien sau it giay:
    echo   https://bisaitextile.streamlit.app
    echo =====================================================================
) else (
    echo =====================================================================
    echo   [CHU Y] Neu GitHub yeu cau Token, hay nhap Personal Access Token
    echo   hoac dang nhap tai khoan GitHub huymaihk tren trinh duyet.
    echo =====================================================================
)
pause

