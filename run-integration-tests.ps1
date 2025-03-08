# PowerShell script to run integration tests for all services
# Usage: .\run-integration-tests.ps1 [service]
# If service is specified, only run tests for that service

param (
    [string]$Service = ""
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to display colored output
function Write-ColorOutput {
    param (
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to run tests for a specific service
function Run-ServiceTests {
    param (
        [string]$ServiceName,
        [string]$Directory
    )
    
    Write-ColorOutput "Running integration tests for $ServiceName..." "Cyan"
    
    # Check if directory exists
    if (-not (Test-Path $Directory)) {
        Write-ColorOutput "Directory not found: $Directory" "Yellow"
        return $false
    }
    
    # Check if tests directory exists
    $TestsDir = Join-Path $Directory "tests\integration"
    if (-not (Test-Path $TestsDir)) {
        Write-ColorOutput "Tests directory not found: $TestsDir" "Yellow"
        return $false
    }
    
    # Run the tests
    try {
        Push-Location $Directory
        Write-ColorOutput "Running tests in $Directory..." "Cyan"
        
        # Install test dependencies if needed
        if (Test-Path "requirements.txt") {
            Write-ColorOutput "Installing dependencies..." "Cyan"
            python -m pip install -r requirements.txt
        }
        
        # Run pytest
        python -m pytest tests\integration -v
        $TestResult = $LASTEXITCODE
        
        if ($TestResult -eq 0) {
            Write-ColorOutput "✅ $ServiceName tests passed!" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ $ServiceName tests failed!" "Red"
            return $false
        }
    } catch {
        Write-ColorOutput "Error running tests: $_" "Red"
        return $false
    } finally {
        Pop-Location
    }
}

# Main script
Write-ColorOutput "=== Running Integration Tests ===" "Magenta"

# Check Python installation
try {
    $PythonVersion = python --version
    Write-ColorOutput "Using $PythonVersion" "Cyan"
} catch {
    Write-ColorOutput "Python not found. Please install Python 3.8 or higher." "Red"
    exit 1
}

# Initialize results tracking
$AllPassed = $true
$Services = @{
    "auth-service" = "backend\auth-service";
    "backend" = "backend\flask-service";
}

# Run tests for specific service or all services
if ($Service) {
    if ($Services.ContainsKey($Service)) {
        $Directory = $Services[$Service]
        $Passed = Run-ServiceTests -ServiceName $Service -Directory $Directory
        $AllPassed = $AllPassed -and $Passed
    } else {
        Write-ColorOutput "Unknown service: $Service" "Red"
        Write-ColorOutput "Available services: $($Services.Keys -join ', ')" "Yellow"
        exit 1
    }
} else {
    # Run tests for all services
    foreach ($ServiceItem in $Services.GetEnumerator()) {
        $Passed = Run-ServiceTests -ServiceName $ServiceItem.Key -Directory $ServiceItem.Value
        $AllPassed = $AllPassed -and $Passed
    }
}

# Display final results
Write-ColorOutput "`n=== Integration Test Results ===" "Magenta"
if ($AllPassed) {
    Write-ColorOutput "✅ All integration tests passed!" "Green"
    exit 0
} else {
    Write-ColorOutput "❌ Some integration tests failed!" "Red"
    exit 1
} 