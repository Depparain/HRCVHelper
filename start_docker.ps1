Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " Запуск контейнеров HRCVHelper через Docker Compose" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

docker-compose up --build -d

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " HRCVHelper контейнеры успешно запущены!" -ForegroundColor Green
Write-Host " Frontend Web UI:    http://localhost:8501" -ForegroundColor Yellow
Write-Host " API Gateway Docs:   http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host " MinIO S3 Console:   http://localhost:9001" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
