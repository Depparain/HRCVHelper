Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Запуск тестов HRCVHelper (pytest)" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

if (Test-Path ".venv\Scripts\pytest.exe") {
    & ".venv\Scripts\pytest.exe" -v
} else {
    pytest -v
}
