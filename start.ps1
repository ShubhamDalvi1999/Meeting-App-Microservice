# Function to check if a command exists
function Test-Command {
    param($Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try { if (Get-Command $Command) { return $true } }
    catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
}

# Check for required tools
Write-Host "Checking required tools..."
$requiredTools = @("docker", "docker-compose", "node", "npm")
foreach ($tool in $requiredTools) {
    if (-not (Test-Command $tool)) {
        Write-Host "Error: $tool is not installed" -ForegroundColor Red
        exit 1
    }
}

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Host "Error: .env file not found" -ForegroundColor Red
    exit 1
}

# Function to wait for service health
function Wait-ServiceHealth {
    param($Service)
    $maxAttempts = 30
    $attempt = 1

    Write-Host "Waiting for $Service to be healthy..."
    while ($attempt -le $maxAttempts) {
        $status = docker-compose ps $Service | Select-String "healthy"
        if ($status) {
            Write-Host "$Service is healthy!" -ForegroundColor Green
            return $true
        }
        Write-Host "Attempt $attempt/$maxAttempts: $Service is not ready yet..."
        Start-Sleep -Seconds 5
        $attempt++
    }
    Write-Host "Error: $Service failed to become healthy" -ForegroundColor Red
    return $false
}

# Stop any running containers
Write-Host "Stopping any existing containers..."
docker-compose down

# Build and start the services
Write-Host "Building and starting services..."
docker-compose up --build -d

# Wait for core services
$services = @("postgres", "redis", "auth-db", "auth-service", "backend", "websocket", "frontend")
foreach ($service in $services) {
    if (-not (Wait-ServiceHealth $service)) {
        Write-Host "Error: Failed to start $service" -ForegroundColor Red
        docker-compose logs $service
        docker-compose down
        exit 1
    }
}

Write-Host "All services are up and running!" -ForegroundColor Green
Write-Host @"

Application URLs:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Auth Service: http://localhost:5001
- WebSocket: ws://localhost:3001
- Metrics: http://localhost:9090

To view logs: docker-compose logs -f
To stop: docker-compose down

"@ -ForegroundColor Cyan 