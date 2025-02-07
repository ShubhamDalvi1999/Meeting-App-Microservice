# Local Development Setup

This document provides instructions for setting up and running the Meeting App locally using Minikube.

## Prerequisites

### Windows
1. Docker Desktop
   - Version: 4.x or later
   - Enable Kubernetes integration

2. Minikube
   - Version: v1.30.0 or later
   - Installation: `winget install minikube`
   - Memory: At least 8GB RAM allocated
   - CPU: At least 4 cores allocated

3. kubectl
   - Version: v1.26.0 or later
   - Installation: `winget install kubernetes-cli`

4. Node.js
   - Version: 18.x LTS
   - Installation: Download from https://nodejs.org/

5. Python
   - Version: 3.11 or later
   - Installation: Download from https://www.python.org/

## Initial Setup

1. Clone the repository
```bash
git clone https://github.com/your-org/meeting-app.git
cd meeting-app
```

2. Start Minikube
```bash
minikube start --driver=docker --memory=8192 --cpus=4
```

3. Enable required addons
```bash
minikube addons enable ingress
minikube addons enable metrics-server
```

4. Configure Docker environment
```bash
eval $(minikube docker-env)
```

## Running the Application

### 1. Build Docker Images
```bash
# Backend
docker build -t meeting-app-backend:dev ./backend

# Frontend
docker build -t meeting-app-frontend:dev ./frontend
```

### 2. Deploy Services
```bash
# Create namespace
kubectl create namespace meeting-app

# Apply configurations
kubectl apply -f k8s/config/development/

# Verify deployments
kubectl get pods -n meeting-app
```

### 3. Access the Application

#### Frontend
```bash
# Get the URL
minikube service meeting-app-frontend -n meeting-app --url
```

#### Backend API
```bash
# Get the URL
minikube service meeting-app-backend -n meeting-app --url
```

## Development Workflow

### Frontend Development

1. Local development server
```bash
cd frontend
npm install
npm run dev
```

2. Environment variables
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_WS_URL=ws://localhost:3001
```

3. Hot reloading
- Changes will automatically reload in the browser
- TypeScript errors will show in the console

### Backend Development

1. Python virtual environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. Environment variables
```bash
# .env
FLASK_APP=app
FLASK_ENV=development
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/meeting_app
REDIS_URL=redis://:dev_password@localhost:6379/0
```

3. Run development server
```bash
flask run --host=0.0.0.0 --port=5000
```

## Database Access

### PostgreSQL
```bash
# Port forward PostgreSQL
kubectl port-forward service/postgres 5432:5432 -n meeting-app

# Connect using psql
psql -h localhost -U dev_user -d meeting_app
```

### Redis
```bash
# Port forward Redis
kubectl port-forward service/redis 6379:6379 -n meeting-app

# Connect using redis-cli
redis-cli -h localhost -p 6379 -a dev_password
```

## Debugging

### Kubernetes
```bash
# View pod logs
kubectl logs -f <pod-name> -n meeting-app

# Describe pod
kubectl describe pod <pod-name> -n meeting-app

# Shell into container
kubectl exec -it <pod-name> -n meeting-app -- /bin/sh
```

### Application

#### Frontend
1. Browser DevTools
   - Network tab for API requests
   - Console for JavaScript errors
   - React DevTools for component debugging

2. Debug logging
```typescript
// Enable debug logging
localStorage.setItem('debug', 'meeting-app:*');
```

#### Backend
1. Flask debug mode
```bash
export FLASK_DEBUG=1
flask run
```

2. Remote debugging
```python
import debugpy
debugpy.listen(('0.0.0.0', 5678))
```

## Common Issues

### 1. Image Pull Errors
```bash
# Ensure images are built in Minikube's Docker
eval $(minikube docker-env)
docker build ...
```

### 2. Database Connection Issues
```bash
# Check if PostgreSQL is running
kubectl get pods -n meeting-app | grep postgres

# Verify credentials
kubectl get secret meeting-app-secrets -n meeting-app -o yaml
```

### 3. WebSocket Connection Errors
```bash
# Check if WebSocket service is running
kubectl get service meeting-app-backend -n meeting-app

# Verify network policies
kubectl get networkpolicies -n meeting-app
```

## Cleanup

### Stop Services
```bash
# Delete namespace
kubectl delete namespace meeting-app

# Stop Minikube
minikube stop
```

### Delete Everything
```bash
# Delete Minikube cluster
minikube delete
```

## Development Tips

### 1. VSCode Extensions
- Kubernetes
- Docker
- Python
- ESLint
- Prettier

### 2. Git Hooks
```bash
# Install husky
npm install husky --save-dev
npx husky install

# Add pre-commit hook
npx husky add .husky/pre-commit "npm run lint && npm run test"
```

### 3. Code Generation
```bash
# Generate TypeScript types from OpenAPI spec
npm run generate-types

# Generate database migrations
flask db migrate -m "description"
```

### 4. Testing
```bash
# Frontend tests
cd frontend
npm run test

# Backend tests
cd backend
pytest

# E2E tests
npm run cypress
``` 