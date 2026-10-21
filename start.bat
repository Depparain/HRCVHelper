@echo off
chcp 65001 >nul
title HRCVHelper - AI Resume Parser & Formatter

echo ======================================================================
echo   HRCVHelper - Автоматизированная система парсинга и верстки резюме
echo ======================================================================
echo.
echo  [1] Запуск полного стека в Docker Compose (Рекомендуется)
echo  [2] Запуск в локальном режиме без Docker (Native Python)
echo  [3] Запуск автоматических тестов (pytest)
echo  [4] Выход
echo.
set /p choice="Выберите режим запуска [1-4] (по умолчанию 1): "

if "%choice%"=="2" goto LOCAL
if "%choice%"=="3" goto TESTS
if "%choice%"=="4" goto EXIT

:DOCKER
echo.
echo ======================================================================
echo  Запуск контейнеров через Docker Compose...
echo ======================================================================
docker compose up --build -d
echo.
echo ======================================================================
echo  Сервисы HRCVHelper успешно запущены!
echo    - Веб-интерфейс:     http://localhost:8501
echo    - API Gateway Docs:  http://localhost:8000/docs
echo    - MinIO S3 Console:  http://localhost:9001
echo ======================================================================
echo.
pause
goto EXIT

:LOCAL
echo.
echo ======================================================================
echo  Запуск в локальном режиме без Docker...
echo ======================================================================
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run_local.py
) else (
    python run_local.py
)
pause
goto EXIT

:TESTS
echo.
echo ======================================================================
echo  Запуск тестов pytest...
echo ======================================================================
if exist .venv\Scripts\pytest.exe (
    .venv\Scripts\pytest.exe -v
) else (
    pytest -v
)
pause
goto EXIT

:EXIT
