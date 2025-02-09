# Function to check if a command exists
function Test-Command {
    param($Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try { if (Get-Command $Command) { return $true } }
    catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
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
        Write-Host "Attempt $attempt of $maxAttempts`: $Service is not ready yet..."
        Start-Sleep -Seconds 5
        $attempt++
    }
    Write-Host "Error: $Service failed to become healthy" -ForegroundColor Red
    return $false
}

# Check for required tools
Write-Host "Checking required tools..." -ForegroundColor Cyan
$requiredTools = @("docker", "docker-compose", "node", "npm")
foreach ($tool in $requiredTools) {
    if (-not (Test-Command $tool)) {
        Write-Host "Error: $tool is not installed" -ForegroundColor Red
        exit 1
    }
}
Write-Host "All required tools are installed" -ForegroundColor Green

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from template..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    Write-Host "Created .env file. Please update it with your configurations." -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "Creating necessary directories..." -ForegroundColor Cyan
$directories = @(
    "logs",
    "logs/auth-service",
    "logs/backend",
    "logs/websocket",
    "data/postgres",
    "data/redis",
    "data/auth-db"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Green
    }
}

# Stop any running containers
Write-Host "Stopping any existing containers..." -ForegroundColor Cyan
docker-compose down

# Build and start core services first
Write-Host "Starting core services..." -ForegroundColor Cyan
docker-compose up -d postgres redis auth-db
Start-Sleep -Seconds 10

# Wait for core services
$coreServices = @("postgres", "redis", "auth-db")
foreach ($service in $coreServices) {
    if (-not (Wait-ServiceHealth $service)) {
        Write-Host "Error: Failed to start core service $service" -ForegroundColor Red
        docker-compose logs $service
        docker-compose down
        exit 1
    }
}

# Start auth service
Write-Host "Starting auth service..." -ForegroundColor Cyan
docker-compose up -d auth-service
if (-not (Wait-ServiceHealth "auth-service")) {
    Write-Host "Error: Failed to start auth-service" -ForegroundColor Red
    docker-compose logs auth-service
    docker-compose down
    exit 1
}

# Run auth service migrations
Write-Host "Running auth service migrations..." -ForegroundColor Cyan
docker-compose exec -T auth-service flask db upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Auth service migrations failed" -ForegroundColor Red
    exit 1
}

# Start remaining services
Write-Host "Starting remaining services..." -ForegroundColor Cyan
docker-compose up -d backend websocket frontend

# Wait for remaining services
$remainingServices = @("backend", "websocket", "frontend")
foreach ($service in $remainingServices) {
    if (-not (Wait-ServiceHealth $service)) {
        Write-Host "Error: Failed to start $service" -ForegroundColor Red
        docker-compose logs $service
        docker-compose down
        exit 1
    }
}

# Run backend migrations
Write-Host "Running backend migrations..." -ForegroundColor Cyan
docker-compose exec -T backend flask db upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Backend migrations failed" -ForegroundColor Red
    exit 1
}

Write-Host @"

🎉 Setup completed successfully! 🎉

Application URLs:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Auth Service: http://localhost:5001
- WebSocket: ws://localhost:3001
- Metrics: http://localhost:9090

Useful commands:
- View logs: docker-compose logs -f
- Stop services: docker-compose down
- Restart services: docker-compose restart
- View specific service logs: docker-compose logs -f [service_name]

"@ -ForegroundColor Green 