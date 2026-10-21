@echo off
echo ======================================================================
echo  Starting HRCVHelper (Native Local Mode without Docker)...
echo ======================================================================

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run_local.py
) else (
    python run_local.py
)

pause
