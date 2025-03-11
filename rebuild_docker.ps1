# Stop and remove all containers
Write-Host "Stopping and removing all containers..." -ForegroundColor Green
docker-compose down

# Remove all images related to the project
Write-Host "Removing all project images..." -ForegroundColor Green
docker rmi fullstackmeetingappwithlogin-backend fullstackmeetingappwithlogin-auth-service fullstackmeetingappwithlogin-frontend fullstackmeetingappwithlogin-websocket -f

# Clean Docker build cache
Write-Host "Cleaning Docker build cache..." -ForegroundColor Green
docker builder prune -f

# Rebuild all images without cache
Write-Host "Rebuilding all images without cache..." -ForegroundColor Green
docker-compose build --no-cache

# Start all services
Write-Host "Starting all services..." -ForegroundColor Green
docker-compose up -d

# Display container status
Write-Host "Container status:" -ForegroundColor Green
docker-compose ps

Write-Host "Rebuild complete! Check logs with 'docker-compose logs -f'" -ForegroundColor Green 