# Meeting Application

A comprehensive meeting management application with authentication, real-time communication, and calendar integration.

## System Architecture

The application is built using a microservices architecture consisting of:

- **Frontend**: Next.js application for the user interface
- **Backend API**: Flask-based API for meeting management
- **Auth Service**: Flask-based microservice for authentication and user management
- **WebSocket Service**: Node.js-based WebSocket server for real-time communication
- **Databases**: PostgreSQL for persistent data storage
- **Redis**: For caching, pub/sub messaging, and session storage
- **Monitoring**: Prometheus and Grafana for metrics and monitoring

## Prerequisites

- Docker and Docker Compose
- Git
- Make (optional, for using Makefile)

### Windows-Specific Requirements

- Docker Desktop with WSL2 backend recommended
- PowerShell 5.0 or higher for running scripts
- Git Bash or WSL2 for bash scripts (optional)

## Quick Start

### Setting Up Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/meeting-app.git
   cd meeting-app
   ```

2. Create a `.env` file by copying the example:
   ```bash
   # For Linux/macOS
   cp .env.example .env
   
   # For Windows
   copy .env.example .env
   ```

3. Modify the `.env` file with your desired configuration values.

### Starting the Application

#### Using Scripts (Recommended)

For Windows:
```powershell
# Ensure PowerShell execution policy allows running scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the start script
.\start.ps1
```

For Linux/macOS:
```bash
# Make the script executable
chmod +x start.sh

# Run the start script
./start.sh
```

#### Manual Startup

Start the services in the following order:

```bash
# 1. Start database services
docker-compose up -d postgres auth-db redis

# 2. Wait for databases to initialize
sleep 15

# 3. Start the auth service
docker-compose up -d auth-service

# 4. Wait for auth service
sleep 10

# 5. Start the backend service
docker-compose up -d backend

# 6. Start remaining services
docker-compose up -d websocket frontend prometheus grafana
```

### Database Migrations

Run migrations to initialize the database schema:

For Windows:
```powershell
.\migrate.ps1 -ForceInit -Upgrade
```

For Linux/macOS:
```bash
chmod +x migrate.sh
./migrate.sh --force-init --upgrade
```

## Accessing the Application

Once all services are started, you can access the application at:

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:5000](http://localhost:5000)
- **Auth Service**: [http://localhost:5001](http://localhost:5001)
- **WebSocket Service**: [http://localhost:3001](http://localhost:3001)
- **Prometheus**: [http://localhost:9090](http://localhost:9090)
- **Grafana**: [http://localhost:3002](http://localhost:3002)

## Development

### Rebuilding Services

If you need to rebuild a specific service after code changes:

```bash
docker-compose build <service-name>
docker-compose up -d <service-name>
```

### Viewing Logs

To view logs for a specific service:

```bash
docker-compose logs <service-name>
```

To follow logs in real-time:

```bash
docker-compose logs -f <service-name>
```

### Running Tests

```bash
docker-compose -f docker-compose.test.yml up
```

## Troubleshooting

For common issues and solutions, please refer to the [Troubleshooting Guide](TROUBLESHOOTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 