# Troubleshooting Guide

## Common Issues and Solutions

### 1. Docker Issues

#### Services won't start
```powershell
# Check Docker status
docker info

# Reset Docker Desktop
# 1. Right-click Docker Desktop icon
# 2. Select "Restart"
# 3. Wait for Docker to fully restart

# Clean up Docker system
docker system prune -a --volumes
```

#### Port conflicts
```powershell
# Check which process is using a port (example: 3000)
netstat -ano | findstr :3000

# Kill process by PID
taskkill /PID <PID> /F
```

### 2. Database Issues

#### Connection errors
```powershell
# Check database logs
docker-compose logs postgres
docker-compose logs auth-db

# Connect to database directly
docker-compose exec postgres psql -U dev_user -d meetingapp
docker-compose exec auth-db psql -U postgres -d auth_db

# Reset database
docker-compose down -v
docker-compose up -d postgres auth-db
```

#### Migration issues
```powershell
# Run migrations manually for Flask service
docker-compose exec backend flask db upgrade

# Run migrations manually for Auth service
docker-compose exec auth-service flask db upgrade
```

### 3. Redis Issues

#### Connection errors
```powershell
# Check Redis logs
docker-compose logs redis

# Connect to Redis CLI
docker-compose exec redis redis-cli -a dev-redis-123

# Clear Redis cache
docker-compose exec redis redis-cli -a dev-redis-123 FLUSHALL
```

### 4. Service-Specific Issues

#### Frontend issues
```powershell
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Clear Next.js cache
docker-compose exec frontend rm -rf .next
```

#### Backend API issues
```powershell
# Check backend logs
docker-compose logs backend

# Restart backend service
docker-compose restart backend

# Check backend health
curl http://localhost:5000/health
```

#### Auth Service issues
```powershell
# Check auth service logs
docker-compose logs auth-service

# Restart auth service
docker-compose restart auth-service

# Check auth service health
curl http://localhost:5001/health
```

#### WebSocket issues
```powershell
# Check WebSocket logs
docker-compose logs websocket

# Restart WebSocket service
docker-compose restart websocket

# Check WebSocket health
curl http://localhost:3001/health
```

### 5. Environment Issues

#### Environment variables not loading
1. Check if `.env` file exists in root directory
2. Verify file permissions
3. Ensure no syntax errors in `.env` file
4. Restart all services after `.env` changes:
```powershell
docker-compose down
docker-compose up -d
```

### 6. Performance Issues

#### High CPU/Memory usage
```powershell
# Check resource usage
docker stats

# Restart specific high-usage service
docker-compose restart <service-name>
```

### 7. Network Issues

#### Services can't communicate
```powershell
# Check Docker network
docker network ls
docker network inspect meeting-app_default

# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

### 8. Development Workflow

#### Hot reload not working
1. Verify environment variables:
   - `WATCHPACK_POLLING=true`
   - `CHOKIDAR_USEPOLLING=true`
2. Check volume mounts in `docker-compose.yml`
3. Restart development containers

### 9. Complete Reset

If all else fails, perform a complete reset:
```powershell
# Stop all containers
docker-compose down

# Remove all volumes
docker-compose down -v

# Clean Docker system
docker system prune -a --volumes

# Rebuild and start fresh
docker-compose up --build -d
```

## Getting Help

If you're still experiencing issues:
1. Check the service logs: `docker-compose logs -f`
2. Review the application logs in `logs/` directory
3. Check the GitHub issues
4. Contact the development team 