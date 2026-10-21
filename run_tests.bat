@echo off
echo ======================================================================
echo  Running HRCVHelper Tests...
echo ======================================================================

if exist .venv\Scripts\pytest.exe (
    .venv\Scripts\pytest.exe -v
) else (
    pytest -v
)

pause
