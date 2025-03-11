param(
    [switch]$coverage,
    [switch]$unit,
    [switch]$integration,
    [string]$service,
    [switch]$rebuild
)

# Function to show help
function Show-Help {
    Write-Host @"
Test Runner Script
Usage: ./run_tests.ps1 [-coverage] [-unit] [-integration] [-service <name>] [-rebuild]

Options:
  -coverage      Run tests with coverage report
  -unit          Run only unit tests
  -integration   Run only integration tests
  -service       Specify service to test (auth-service or flask-service)
  -rebuild       Rebuild containers before running tests

Examples:
  ./run_tests.ps1                     # Run all tests
  ./run_tests.ps1 -coverage           # Run all tests with coverage
  ./run_tests.ps1 -unit -service auth # Run auth service unit tests
  ./run_tests.ps1 -rebuild            # Rebuild and run all tests
"@
    exit
}

# Show help if no arguments provided
if ($args.Count -eq 0 -and -not $coverage -and -not $unit -and -not $integration -and -not $service -and -not $rebuild) {
    Show-Help
}

# Base command
$cmd = "docker-compose -f docker-compose.test.yml"

# Add rebuild flag if specified
if ($rebuild) {
    $cmd += " build"
}

# Prepare test command based on flags
$test_cmd = "pytest -v"
if ($coverage) {
    $test_cmd += " --cov=src --cov=meeting_shared --cov-report=term-missing --cov-report=html"
}
if ($unit) {
    $test_cmd += " tests/unit/"
}
if ($integration) {
    $test_cmd += " tests/integration/"
}

# Run tests based on service flag
if ($service) {
    switch ($service) {
        "auth" {
            Write-Host "Running auth-service tests..."
            Invoke-Expression "$cmd run auth-service-tests $test_cmd"
        }
        "flask" {
            Write-Host "Running flask-service tests..."
            Invoke-Expression "$cmd run flask-service-tests $test_cmd"
        }
        default {
            Write-Host "Invalid service specified. Use 'auth' or 'flask'."
            exit 1
        }
    }
} else {
    # Run all services
    Write-Host "Running all tests..."
    Invoke-Expression "$cmd up --abort-on-container-exit"
} 