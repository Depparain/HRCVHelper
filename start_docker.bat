@echo off
echo ======================================================================
echo  Starting HRCVHelper containers via Docker Compose...
echo ======================================================================

docker-compose up --build -d

echo ======================================================================
echo  HRCVHelper containers are running!
echo  Frontend Web UI:   http://localhost:8501
echo  API Gateway Docs:  http://localhost:8000/docs
echo  MinIO S3 Console:  http://localhost:9001
echo ======================================================================

pause
