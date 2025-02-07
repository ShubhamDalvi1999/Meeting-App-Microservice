# Meeting App - WebRTC Based Video Conferencing

A full-stack meeting application built with microservices architecture, featuring video/audio calls, screen sharing, whiteboard, and chat functionality.

## Features

- Video and Audio Calls using WebRTC
- Screen Sharing
- Interactive Whiteboard with multiple colors
- Real-time Chat
- Multiple user support with meeting codes
- Containerized microservices architecture with Kubernetes orchestration

## Tech Stack

- Frontend: Next.js + React + TypeScript
- Backend Services:
  - Flask API Service: User management and business logic
  - Node.js WebSocket Service: Real-time communication
- Database: PostgreSQL
- Cache: Redis
- Containerization: Docker
- Orchestration: Kubernetes

## Prerequisites

- Docker Desktop with Kubernetes enabled
- PowerShell (for Windows)
- kubectl CLI tool
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## Project Structure

```
.
├── frontend/                 # Next.js frontend application
├── backend/
│   ├── flask-service/       # Flask REST API service
│   └── node-service/        # Node.js WebSocket service
├── k8s/                     # Kubernetes configuration files
│   └── config/
│       └── development/     # Development environment configs
├── scripts/                 # Deployment and utility scripts
├── docs/                    # Documentation
└── README.md
```

## Deployment

### Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd meeting-app
   ```

2. Run the deployment script (requires administrator privileges for hosts file modification):
   ```powershell
   # Open PowerShell as Administrator
   .\scripts\deploy-meeting-app.ps1
   ```

3. Access the application:
   - Frontend: http://meeting-app.local:30000
   - API: http://api.meeting-app.local:30963
   - WebSocket: ws://ws.meeting-app.local:30283

### Manual Deployment Steps

1. Build Docker images:
   ```powershell
   docker build -t meeting-app-backend:dev ./backend/flask-service
   docker build -t meeting-app-websocket:dev ./backend/node-service
   docker build -t meeting-app-frontend:dev ./frontend
   ```

2. Create Kubernetes resources:
   ```powershell
   kubectl create namespace meeting-app
   kubectl apply -f k8s/config/development/volumes.yaml -n meeting-app
   kubectl apply -f k8s/config/development/configmap.yaml -n meeting-app
   kubectl apply -f k8s/config/development/secrets.yaml -n meeting-app
   kubectl apply -f k8s/config/development/postgres.yaml -n meeting-app
   kubectl apply -f k8s/config/development/redis.yaml -n meeting-app
   kubectl apply -f k8s/config/development/deployment.yaml -n meeting-app
   kubectl apply -f k8s/config/development/frontend-deployment.yaml -n meeting-app
   kubectl apply -f k8s/config/development/network-policies.yaml -n meeting-app
   kubectl apply -f k8s/config/development/ingress.yaml -n meeting-app
   ```

3. Update hosts file (`C:\Windows\System32\drivers\etc\hosts`):
   ```
   127.0.0.1 meeting-app.local
   127.0.0.1 api.meeting-app.local
   127.0.0.1 ws.meeting-app.local
   ```

## Development

### Local Development Setup

1. Install dependencies:
   ```bash
   # Frontend
   cd frontend
   npm install

   # Flask Backend
   cd backend/flask-service
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt

   # Node.js Backend
   cd backend/node-service
   npm install
   ```

2. Set up environment variables:
   - Copy the example environment files
   - Update the values according to your local setup
   - For Kubernetes deployment, update the ConfigMap in `k8s/config/development/configmap.yaml`

### Useful Commands

```bash
# Check deployment status
kubectl get all -n meeting-app

# View logs
kubectl logs -n meeting-app <pod-name>

# Clean up
kubectl delete namespace meeting-app

# Port forwarding (for local development)
kubectl port-forward -n meeting-app svc/meeting-frontend-internal 3000:3000
kubectl port-forward -n meeting-app svc/meeting-backend-internal 5000:5000
```

## Troubleshooting

1. If pods are stuck in `Pending` state:
   - Check PVC status: `kubectl get pvc -n meeting-app`
   - Verify storage class: `kubectl get sc`
   - Check events: `kubectl get events -n meeting-app`

2. If services are not accessible:
   - Verify NodePort services: `kubectl get svc -n meeting-app`
   - Check ingress status: `kubectl get ingress -n meeting-app`
   - Ensure hosts file is updated correctly

## Contributing

1. Create a feature branch
2. Commit your changes
3. Push to the branch
4. Create a Pull Request

## License

MIT 

## Documentation

For detailed information about the system, please refer to the following documentation:

- [Meeting System Enhancements](docs/meeting_system_enhancements.md) - Details about the latest features and improvements
- [Database Migrations](docs/database_migrations.md) - Information about database schema changes and migrations
- [API Documentation](docs/api.md) - Complete API reference
- [Development Guide](docs/development.md) - Guide for developers 