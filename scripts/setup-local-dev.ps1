# Function to handle errors
function Write-ErrorAndExit {
    param($message)
    Write-Host "Error: $message" -ForegroundColor Red
    exit 1
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "Checking prerequisites..."
    
    # Check if running as Administrator
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-ErrorAndExit "This script must be run as Administrator"
    }
    
    # Check Docker
    try {
        docker version | Out-Null
    } catch {
        Write-ErrorAndExit "Docker is not running. Please start Docker Desktop"
    }
    
    # Check Kubernetes
    try {
        kubectl version | Out-Null
    } catch {
        Write-ErrorAndExit "Kubernetes is not running. Please enable Kubernetes in Docker Desktop"
    }
    
    # Check Minikube
    try {
        minikube status | Out-Null
    } catch {
        Write-ErrorAndExit "Minikube is not running. Please start Minikube"
    }
}

# Function to setup networking
function Setup-Networking {
    Write-Host "Setting up networking..."
    
    # Get Minikube IP
    try {
        $MINIKUBE_IP = minikube ip
        Write-Host "Minikube IP: $MINIKUBE_IP"
    } catch {
        Write-ErrorAndExit "Failed to get Minikube IP"
    }
    
    # Update hosts file
    try {
        $hostsPath = "$env:windir\System32\drivers\etc\hosts"
        $hostsContent = Get-Content $hostsPath
        
        # Backup hosts file
        Copy-Item $hostsPath "$hostsPath.bak"
        
        # Remove old entries
        $hostsContent = $hostsContent | Where-Object { $_ -notmatch 'meeting-app.local' }
        
        # Add new entries
        $newEntries = @"
$MINIKUBE_IP meeting-app.local
$MINIKUBE_IP api.meeting-app.local
$MINIKUBE_IP ws.meeting-app.local
"@
        $newEntries | Add-Content $hostsPath
    } catch {
        Write-ErrorAndExit "Failed to update hosts file"
    }
    
    # Enable ingress
    Write-Host "Enabling ingress addon..."
    minikube addons enable ingress
    
    # Wait for ingress controller
    Write-Host "Waiting for ingress controller..."
    kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=180s
}

# Function to build images
function Build-Images {
    Write-Host "Building Docker images..."
    
    try {
        # Point Docker to Minikube's Docker daemon
        Write-Host "Configuring Docker environment..."
        minikube docker-env | Invoke-Expression
        
        # Build images
        docker build -t meeting-app-frontend:dev ./frontend
        docker build -t meeting-app-backend:dev ./backend/flask-service
        docker build -t meeting-app-websocket:dev ./backend/node-service
    } catch {
        Write-ErrorAndExit "Failed to build Docker images"
    }
}

# Function to deploy services
function Deploy-Services {
    Write-Host "Deploying services..."
    
    try {
        # Apply configurations
        kubectl apply -f k8s/config/development/
        
        # Wait for core services
        Write-Host "Waiting for core services..."
        kubectl wait --for=condition=ready pod -l app=postgres --timeout=180s
        kubectl wait --for=condition=ready pod -l app=redis --timeout=180s
        
        # Initialize database if needed
        Write-Host "Checking database initialization..."
        $dbPod = kubectl get pod -l app=postgres -o jsonpath="{.items[0].metadata.name}"
        $initDbResult = kubectl exec $dbPod -- psql -U dev_user -d meetingapp -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users')" -t
        if ($initDbResult -notmatch "t") {
            Write-Host "Initializing database..."
            kubectl exec $dbPod -- psql -U dev_user -d meetingapp -f /docker-entrypoint-initdb.d/init.sql
        }
        
        # Wait for application services
        Write-Host "Waiting for application services..."
        kubectl wait --for=condition=ready pod -l app=meeting-app --timeout=180s
        kubectl wait --for=condition=ready pod -l app=meeting-app-frontend --timeout=180s
    } catch {
        Write-ErrorAndExit "Failed to deploy services"
    }
}

# Function to verify deployment
function Test-Deployment {
    Write-Host "Verifying deployment..."
    
    # Wait for services to be ready
    Start-Sleep -Seconds 10
    
    # Test endpoints
    try {
        $frontendHealth = Invoke-WebRequest "http://localhost:30000/health" -UseBasicParsing
        $apiHealth = Invoke-WebRequest "http://localhost:30963/health" -UseBasicParsing
        
        if ($frontendHealth.StatusCode -ne 200 -or $apiHealth.StatusCode -ne 200) {
            Write-Host "Warning: Some health checks failed" -ForegroundColor Yellow
        }
        
        # Test database connection
        $dbHealth = Invoke-WebRequest "http://localhost:30963/health/db" -UseBasicParsing
        if ($dbHealth.StatusCode -ne 200) {
            Write-Host "Warning: Database health check failed" -ForegroundColor Yellow
        }
        
        # Test Redis connection
        $redisHealth = Invoke-WebRequest "http://localhost:30963/health/redis" -UseBasicParsing
        if ($redisHealth.StatusCode -ne 200) {
            Write-Host "Warning: Redis health check failed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Warning: Could not verify all endpoints" -ForegroundColor Yellow
    }
}

# Main execution
try {
    Test-Prerequisites
    Setup-Networking
    Build-Images
    Deploy-Services
    Test-Deployment
    
    Write-Host @"
Local Kubernetes development environment is ready!

Access Methods:
1. Port-based access (recommended for local development):
   - Frontend: http://localhost:30000
   - API: http://localhost:30963
   - WebSocket: ws://localhost:30283

2. Domain-based access (alternative):
   - Frontend: http://meeting-app.local
   - API: http://api.meeting-app.local
   - WebSocket: ws://ws.meeting-app.local

Internal Services:
- PostgreSQL: Running in cluster
- Redis: Running in cluster

Monitoring:
- Kubernetes Dashboard: Run 'minikube dashboard'
- Grafana: http://localhost:3000 (admin/admin123)

Useful Commands:
- View pods: kubectl get pods
- View logs: kubectl logs <pod-name>
- Shell access: kubectl exec -it <pod-name> -- /bin/sh
- View services: kubectl get services
- View ingress: kubectl get ingress

Keep this terminal window open to maintain port forwarding.
Press Enter to stop and cleanup.
"@

    # Wait for user input
    Read-Host "Press Enter to stop the local development environment..."
} catch {
    Write-ErrorAndExit $_.Exception.Message
} finally {
    # Cleanup
    Write-Host "Cleaning up..."
    Get-Job | Stop-Job
    Get-Job | Remove-Job
} 