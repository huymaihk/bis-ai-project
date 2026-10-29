@echo off
title BIS Textile AI - Multi-Agent Team Portal
cls
echo =================================================================
echo   BIS TEXTILE AI — HE THONG MULTI-AGENT TEAM (v3.0)
echo   Leader - Technical - Operations - Learning Loop - UI
echo =================================================================
echo.
echo [1] Khoi chay Giao dien Web Noi bo (Streamlit Dashboard: app_ui.py)
echo [2] Chay Pipeline trich xuat Catalogue PDF (Agent_Leader)
echo [3] Dong bo cac san pham APPROVED len Haravan (Agent_Operations)
echo [4] Mo Ban Duyet San Pham HTML cuc bo (bis_review_workspace.html)
echo [5] Xem Bo nho Tu hoc (feedback_memory.json)
echo [6] Thoat
echo.
set /p opt="Chon thao tac (1-6): "

if "%opt%"=="1" (
    echo.
    echo Dang khoi chay Streamlit Web Dashboard...
    py -3.15 -m streamlit run app_ui.py
    pause
    goto end
)
if "%opt%"=="2" (
    echo.
    py -3.15 main_pipeline.py
    pause
    goto end
)
if "%opt%"=="3" (
    echo.
    echo [CANH BAO] Ban sap day cac san pham APPROVED len Haravan o che do AN!
    set /p confirm="Ban co chac chan muon tiep tuc? (y/n): "
    if /i "%confirm%"=="y" (
        py -3.15 main_pipeline.py --sync-haravan
    ) else (
        echo Da huy thao tac.
    )
    pause
    goto end
)
if "%opt%"=="4" (
    start bis_review_workspace.html
    goto end
)
if "%opt%"=="5" (
    type feedback_memory.json
    pause
    goto end
)

:end
