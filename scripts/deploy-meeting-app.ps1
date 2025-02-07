# Simple deployment script for Meeting App
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "🚀 Cleaning up previous deployment..." -ForegroundColor Cyan

try {
    # Clean up previous deployment
    Write-Host "1️⃣ Removing previous Kubernetes resources..." -ForegroundColor Cyan
    kubectl delete -f k8s/config/development/ --ignore-not-found
    kubectl delete namespace meeting-app --ignore-not-found
    
    Write-Host "2️⃣ Cleaning up Docker containers..." -ForegroundColor Cyan
    docker ps -aq | ForEach-Object { docker stop $_ }
    docker container prune -f
    
    Start-Sleep -Seconds 5  # Wait for resources to be cleaned up
    
    Write-Host "🚀 Starting fresh deployment..." -ForegroundColor Cyan
    
    # 1. Set environment variables
    Write-Host "3️⃣ Setting environment variables..." -ForegroundColor Cyan
    .\scripts\Set-Environment.ps1 -Environment development
    
    # 2. Build Docker images
    Write-Host "4️⃣ Building Docker images..." -ForegroundColor Cyan
    docker build -t meeting-app-backend:dev -f backend/flask-service/Dockerfile ./backend/flask-service
    docker build -t meeting-app-frontend:dev -f frontend/Dockerfile ./frontend
    
    # 3. Apply Kubernetes configurations
    Write-Host "5️⃣ Applying Kubernetes configurations..." -ForegroundColor Cyan
    
    # Create namespace if it doesn't exist
    kubectl create namespace meeting-app --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    kubectl apply -f k8s/config/development/configmap.yaml
    kubectl apply -f k8s/config/development/secrets.yaml
    kubectl apply -f k8s/config/development/deployment.yaml
    
    # 4. Verify deployment
    Write-Host "6️⃣ Verifying deployment..." -ForegroundColor Cyan
    Write-Host "`nServices:" -ForegroundColor Yellow
    kubectl get services
    
    Write-Host "`nPods:" -ForegroundColor Yellow
    kubectl get pods
    
    Write-Host "`n✅ Deployment completed!" -ForegroundColor Green
    Write-Host @"

🌐 Access the application:
   Frontend: http://localhost:30000
   API: http://localhost:30963
   WebSocket: ws://localhost:30283

📋 Useful commands:
   - View all resources: kubectl get all
   - View logs: kubectl logs <pod-name>
   - Delete all: kubectl delete -f k8s/config/development/
"@ -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Deployment failed: $_" -ForegroundColor Red
    exit 1
} 