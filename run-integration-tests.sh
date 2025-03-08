#!/bin/bash
# Bash script to run integration tests for all services
# Usage: ./run-integration-tests.sh [service]
# If service is specified, only run tests for that service

# Exit on error
set -e

# Function to display colored output
function print_color() {
    local color=$1
    local message=$2
    
    case $color in
        "red")
            echo -e "\033[0;31m$message\033[0m"
            ;;
        "green")
            echo -e "\033[0;32m$message\033[0m"
            ;;
        "yellow")
            echo -e "\033[0;33m$message\033[0m"
            ;;
        "blue")
            echo -e "\033[0;34m$message\033[0m"
            ;;
        "magenta")
            echo -e "\033[0;35m$message\033[0m"
            ;;
        "cyan")
            echo -e "\033[0;36m$message\033[0m"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# Function to run tests for a specific service
function run_service_tests() {
    local service_name=$1
    local directory=$2
    
    print_color "cyan" "Running integration tests for $service_name..."
    
    # Check if directory exists
    if [ ! -d "$directory" ]; then
        print_color "yellow" "Directory not found: $directory"
        return 1
    fi
    
    # Check if tests directory exists
    local tests_dir="$directory/tests/integration"
    if [ ! -d "$tests_dir" ]; then
        print_color "yellow" "Tests directory not found: $tests_dir"
        return 1
    fi
    
    # Run the tests
    pushd "$directory" > /dev/null
    print_color "cyan" "Running tests in $directory..."
    
    # Install test dependencies if needed
    if [ -f "requirements.txt" ]; then
        print_color "cyan" "Installing dependencies..."
        python -m pip install -r requirements.txt
    fi
    
    # Run pytest
    python -m pytest tests/integration -v
    local test_result=$?
    
    if [ $test_result -eq 0 ]; then
        print_color "green" "✅ $service_name tests passed!"
        popd > /dev/null
        return 0
    else
        print_color "red" "❌ $service_name tests failed!"
        popd > /dev/null
        return 1
    fi
}

# Main script
print_color "magenta" "=== Running Integration Tests ==="

# Check Python installation
if ! command -v python &> /dev/null; then
    print_color "red" "Python not found. Please install Python 3.8 or higher."
    exit 1
fi

python_version=$(python --version)
print_color "cyan" "Using $python_version"

# Initialize results tracking
all_passed=true
declare -A services
services["auth-service"]="backend/auth-service"
services["backend"]="backend/flask-service"

# Run tests for specific service or all services
if [ $# -gt 0 ]; then
    service=$1
    if [ -n "${services[$service]}" ]; then
        directory=${services[$service]}
        if ! run_service_tests "$service" "$directory"; then
            all_passed=false
        fi
    else
        print_color "red" "Unknown service: $service"
        print_color "yellow" "Available services: ${!services[*]}"
        exit 1
    fi
else
    # Run tests for all services
    for service in "${!services[@]}"; do
        directory=${services[$service]}
        if ! run_service_tests "$service" "$directory"; then
            all_passed=false
        fi
    done
fi

# Display final results
print_color "magenta" $'\n=== Integration Test Results ==='
if $all_passed; then
    print_color "green" "✅ All integration tests passed!"
    exit 0
else
    print_color "red" "❌ Some integration tests failed!"
    exit 1
fi 