# Start.ps1 - Enforces the correct startup sequence for the meeting application

Write-Host "Starting database services..." -ForegroundColor Green
docker-compose up -d postgres auth-db redis
Write-Host "Waiting for database services to be ready (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "Starting authentication service..." -ForegroundColor Green
docker-compose up -d auth-service
Write-Host "Waiting for authentication service to initialize (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Starting backend service..." -ForegroundColor Green
docker-compose up -d backend
Write-Host "Waiting for backend service to initialize (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "Starting websocket service..." -ForegroundColor Green
docker-compose up -d websocket
Write-Host "Waiting for websocket service to initialize (5 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Starting frontend service..." -ForegroundColor Green
docker-compose up -d frontend

Write-Host "Starting monitoring services..." -ForegroundColor Green
docker-compose up -d prometheus grafana

Write-Host "All services started. Check status with: docker-compose ps" -ForegroundColor Cyan
docker-compose ps

Write-Host "Application is now available at:" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend API: http://localhost:5000" -ForegroundColor Cyan
Write-Host "  Auth API: http://localhost:5001" -ForegroundColor Cyan
Write-Host "  WebSocket: http://localhost:3001" -ForegroundColor Cyan
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor Cyan
Write-Host "  Grafana: http://localhost:3002" -ForegroundColor Cyan 