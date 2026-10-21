Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Запуск HRCVHelper (Native Local Mode без Docker)" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

if (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" run_local.py
} else {
    python run_local.py
}
