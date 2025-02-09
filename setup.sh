#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service health
wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1

    echo -e "${CYAN}Waiting for $service to be healthy...${NC}"
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps "$service" | grep -q "healthy"; then
            echo -e "${GREEN}$service is healthy!${NC}"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: $service is not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    done
    echo -e "${RED}Error: $service failed to become healthy${NC}"
    return 1
}

# Check for required tools
echo -e "${CYAN}Checking required tools...${NC}"
required_tools=("docker" "docker-compose" "node" "npm")
for tool in "${required_tools[@]}"; do
    if ! command_exists "$tool"; then
        echo -e "${RED}Error: $tool is not installed${NC}"
        exit 1
    fi
done
echo -e "${GREEN}All required tools are installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${CYAN}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Created .env file. Please update it with your configurations.${NC}"
fi

# Create necessary directories
echo -e "${CYAN}Creating necessary directories...${NC}"
directories=(
    "logs"
    "logs/auth-service"
    "logs/backend"
    "logs/websocket"
    "data/postgres"
    "data/redis"
    "data/auth-db"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}Created directory: $dir${NC}"
    fi
done

# Stop any running containers
echo -e "${CYAN}Stopping any existing containers...${NC}"
docker-compose down

# Build and start core services first
echo -e "${CYAN}Starting core services...${NC}"
docker-compose up -d postgres redis auth-db
sleep 10

# Wait for core services
core_services=("postgres" "redis" "auth-db")
for service in "${core_services[@]}"; do
    if ! wait_for_service "$service"; then
        echo -e "${RED}Error: Failed to start core service $service${NC}"
        docker-compose logs "$service"
        docker-compose down
        exit 1
    fi
done

# Start auth service
echo -e "${CYAN}Starting auth service...${NC}"
docker-compose up -d auth-service
if ! wait_for_service "auth-service"; then
    echo -e "${RED}Error: Failed to start auth-service${NC}"
    docker-compose logs auth-service
    docker-compose down
    exit 1
fi

# Run auth service migrations
echo -e "${CYAN}Running auth service migrations...${NC}"
if ! docker-compose exec -T auth-service flask db upgrade; then
    echo -e "${RED}Error: Auth service migrations failed${NC}"
    exit 1
fi

# Start remaining services
echo -e "${CYAN}Starting remaining services...${NC}"
docker-compose up -d backend websocket frontend

# Wait for remaining services
remaining_services=("backend" "websocket" "frontend")
for service in "${remaining_services[@]}"; do
    if ! wait_for_service "$service"; then
        echo -e "${RED}Error: Failed to start $service${NC}"
        docker-compose logs "$service"
        docker-compose down
        exit 1
    fi
done

# Run backend migrations
echo -e "${CYAN}Running backend migrations...${NC}"
if ! docker-compose exec -T backend flask db upgrade; then
    echo -e "${RED}Error: Backend migrations failed${NC}"
    exit 1
fi

# Print success message
echo -e "${GREEN}
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
${NC}" 