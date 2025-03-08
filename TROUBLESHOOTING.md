# Troubleshooting Guide

This document outlines common issues you might encounter when setting up or running the Meeting Application and provides solutions for resolving them.

## Table of Contents

1. [Docker Issues](#docker-issues)
2. [Database Issues](#database-issues)
3. [Service Connectivity Issues](#service-connectivity-issues)
4. [Authentication Issues](#authentication-issues)
5. [Frontend Issues](#frontend-issues)
6. [Windows-Specific Issues](#windows-specific-issues)

## Docker Issues

### Issue: Docker containers fail to build

**Symptoms:**
- `docker-compose build` fails with permission errors or "unknown file mode" errors
- Errors about missing files during build

**Solutions:**
- Make sure you're using the correct `.dockerignore` files in each service directory
- On Windows, use `Dockerfile.fixed` for the backend service
- On Windows, try using Docker Desktop with WSL2 backend for better compatibility
- Ensure line endings are consistent (LF, not CRLF) in scripts copied to containers

### Issue: Docker containers exit immediately after starting

**Symptoms:**
- `docker-compose up` shows containers starting but then stopping
- `docker-compose ps` shows containers in "Exit" state

**Solutions:**
- Check container logs with `docker-compose logs <service-name>`
- Verify environment variables are properly set in `.env` file
- Make sure entrypoint scripts have proper execute permissions
- Ensure database connectivity (containers may exit if DB connection fails)

### Issue: Services can't connect to each other

**Symptoms:**
- Logs show connection refused errors
- Services can't find each other by hostname

**Solutions:**
- Ensure all services are on the same Docker network
- Use correct service hostnames (as defined in docker-compose.yml)
- Verify ports are exposed correctly
- Check that service dependencies are properly defined in docker-compose.yml

## Database Issues

### Issue: Database migrations fail

**Symptoms:**
- Flask migrations show "Multiple heads" error
- Services exit with "database not ready" or "database not initialized"

**Solutions:**
- Merge migration heads using `./migrate.ps1 -Merge` or `./migrate.sh --merge`
- Verify database credentials in `.env` file
- Check that migrations are properly initialized with `./migrate.ps1 -ForceInit`
- Ensure PostgreSQL is running and accessible

### Issue: Database connection timeouts

**Symptoms:**
- Services report "database connection timeout"
- Intermittent database errors

**Solutions:**
- Increase healthcheck timeouts and retries in docker-compose.yml
- Ensure PostgreSQL has adequate resources
- Check for network issues between services
- Verify connection string format in environment variables

## Service Connectivity Issues

### Issue: Auth service not responding

**Symptoms:**
- Authentication fails
- Backend logs show auth service connectivity issues

**Solutions:**
- Check if auth-service is running with `docker-compose ps`
- Verify `AUTH_SERVICE_URL` environment variable is set correctly
- Ensure auth-service is healthy with `curl http://localhost:5001/health`
- Check auth-service logs with `docker-compose logs auth-service`

### Issue: Backend API not accessible

**Symptoms:**
- Frontend can't connect to backend
- `curl http://localhost:5000/health` fails

**Solutions:**
- Verify backend service is running with `docker-compose ps`
- Check backend logs with `docker-compose logs backend`
- Ensure port 5000 is exposed and not blocked by firewall
- Verify `NEXT_PUBLIC_API_URL` is set correctly for frontend

## Authentication Issues

### Issue: JWT token validation fails

**Symptoms:**
- Users get logged out unexpectedly
- API requests return 401 Unauthorized

**Solutions:**
- Ensure `JWT_SECRET_KEY` is identical across all services
- Check token expiration settings
- Verify clock synchronization between services
- Make sure `SERVICE_KEY` for inter-service communication is correct

### Issue: User registration fails

**Symptoms:**
- New users can't register
- Registration form submits but returns errors

**Solutions:**
- Check auth-service logs
- Verify email validation settings
- Ensure database connectivity for auth-service
- Check for duplicate email prevention logic

## Frontend Issues

### Issue: Frontend fails to build

**Symptoms:**
- `docker-compose build frontend` fails
- Next.js build errors

**Solutions:**
- Check for proper Node.js version in frontend Dockerfile
- Ensure all dependencies are correctly installed
- Verify proper volume mounts for node_modules
- Check if `.next` directory has correct permissions

### Issue: Frontend can't connect to backend services

**Symptoms:**
- API requests fail
- Console shows CORS errors or connection refused

**Solutions:**
- Verify environment variables in frontend service:
  - `NEXT_PUBLIC_API_URL`
  - `NEXT_PUBLIC_WS_URL`
  - `NEXT_PUBLIC_AUTH_URL`
- Ensure CORS is properly configured in backend and auth services
- Check network connectivity between containers

## Windows-Specific Issues

### Issue: File permission errors in Docker

**Symptoms:**
- "unknown file mode" errors
- Permission denied when copying files

**Solutions:**
- Use `.dockerignore` files to exclude problem files/directories
- Use explicit COPY commands in Dockerfile rather than copying entire directories
- Set Git to use LF line endings: `git config --global core.autocrlf input`
- Use Docker Desktop with WSL2 backend

### Issue: Scripts won't execute

**Symptoms:**
- PowerShell scripts show security errors
- Bash scripts fail with "bad interpreter"

**Solutions:**
- For PowerShell: Set execution policy with `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- For bash scripts in Windows: Use `bash script.sh` instead of `./script.sh`
- Ensure scripts have correct line endings (LF for bash scripts)
- Make sure scripts have executable permission: `chmod +x script.sh` (in WSL or Git Bash)

## Getting Help

If you're still experiencing issues:
1. Check the service logs: `docker-compose logs -f`
2. Review the application logs in `logs/` directory
3. Check the GitHub issues
4. Contact the development team 