# migrate.ps1 - Database migration management for the meeting application

param (
    [switch]$ShowCurrent,
    [switch]$Upgrade,
    [switch]$Merge,
    [switch]$ForceInit
)

function Show-Help {
    Write-Host "Database Migration Management Script" -ForegroundColor Cyan
    Write-Host "Usage: ./migrate.ps1 [options]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -ShowCurrent  : Show current migration versions" -ForegroundColor Gray
    Write-Host "  -Upgrade      : Apply all pending migrations" -ForegroundColor Gray
    Write-Host "  -Merge        : Merge migration heads if multiple heads exist" -ForegroundColor Gray
    Write-Host "  -ForceInit    : Force initialize migrations if they don't exist" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Example: ./migrate.ps1 -Upgrade" -ForegroundColor Green
}

# Check if any param was passed, otherwise show help
if (-not ($ShowCurrent -or $Upgrade -or $Merge -or $ForceInit)) {
    Show-Help
    exit 0
}

# Show current migration versions
if ($ShowCurrent) {
    Write-Host "Checking current migration state for backend..." -ForegroundColor Green
    docker-compose exec -T backend flask db current
    
    Write-Host "Checking current migration state for auth-service..." -ForegroundColor Green
    docker-compose exec -T auth-service flask db current
}

# Force initialize migrations if they don't exist
if ($ForceInit) {
    Write-Host "Force initializing migrations for backend (if needed)..." -ForegroundColor Yellow
    docker-compose exec -T backend bash -c "if [ ! -f migrations/alembic.ini ]; then flask db init; fi"
    
    Write-Host "Force initializing migrations for auth-service (if needed)..." -ForegroundColor Yellow
    docker-compose exec -T auth-service bash -c "if [ ! -f migrations/alembic.ini ]; then flask db init; fi"
}

# Merge migration heads if multiple heads exist
if ($Merge) {
    Write-Host "Merging migration heads for backend..." -ForegroundColor Yellow
    docker-compose exec -T backend flask db merge heads -m "merge_migration_heads"
    
    Write-Host "Merging migration heads for auth-service..." -ForegroundColor Yellow
    docker-compose exec -T auth-service flask db merge heads -m "merge_migration_heads"
}

# Apply all pending migrations
if ($Upgrade) {
    Write-Host "Applying pending migrations for backend..." -ForegroundColor Green
    docker-compose exec -T backend flask db upgrade
    
    Write-Host "Applying pending migrations for auth-service..." -ForegroundColor Green
    docker-compose exec -T auth-service flask db upgrade
}

Write-Host "Migration operations completed" -ForegroundColor Cyan 