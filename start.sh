#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo "Checking required tools..."
for cmd in docker docker-compose node npm python pip; do
    if ! command_exists $cmd; then
        echo "Error: $cmd is not installed"
        exit 1
    fi
done

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# Function to wait for service health
wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1

    echo "Waiting for $service to be healthy..."
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy"; then
            echo "$service is healthy!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: $service is not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    done
    echo "Error: $service failed to become healthy"
    return 1
}

# Stop any running containers
echo "Stopping any existing containers..."
docker-compose down

# Build and start the services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for core services
for service in postgres redis auth-db auth-service backend websocket frontend; do
    if ! wait_for_service $service; then
        echo "Error: Failed to start $service"
        docker-compose logs $service
        docker-compose down
        exit 1
    fi
done

echo "All services are up and running!"
echo "
Application URLs:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Auth Service: http://localhost:5001
- WebSocket: ws://localhost:3001
- Metrics: http://localhost:9090

To view logs: docker-compose logs -f
To stop: docker-compose down
" 