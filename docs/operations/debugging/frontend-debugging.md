# Frontend Access Debugging Documentation

## Initial Problem
The frontend application was inaccessible with two main issues:
1. "This site can't be reached" error when trying to access the application
2. Module resolution error: `Can't resolve '@/contexts/AuthContext'`

## Root Causes Identified

### 1. Path Alias Configuration Issue
- The `@` path alias in Next.js wasn't properly configured
- The `tsconfig.json` and `next.config.js` had mismatched configurations
- This caused the application to fail when trying to import the `AuthContext`

### 2. Missing App Provider
- The `_app.tsx` file was empty
- The `AuthProvider` wasn't wrapping the application
- This would have caused authentication issues even if the application loaded

### 3. Port Access Issues
- Port 30000 was already in use
- Port forwarding wasn't properly set up
- This prevented access to the application through localhost

## Solutions Applied

### 1. Fixed Path Alias Configuration
```typescript
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": "./src",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### 2. Created Proper App Provider
```typescript
// _app.tsx
import { AppProps } from 'next/app';
import { AuthProvider } from '../contexts/AuthContext';
import '../styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

export default MyApp;
```

### 3. Fixed Port Forwarding
```bash
# Changed from port 30000 to 8080 to avoid conflicts
kubectl port-forward service/meeting-app-frontend-external 8080:3000
```

## Why It Worked

### Path Resolution
- Changed the base URL in `tsconfig.json` to `./src`
- This allowed Next.js to correctly resolve imports from the `src` directory
- The relative import path `../contexts/AuthContext` now works correctly

### Application Context
- The `AuthProvider` now properly wraps all components
- This ensures the authentication context is available throughout the application

### Port Access
- Using port 8080 instead of 30000 avoided port conflicts
- The port forwarding successfully routes traffic to the pod

## Current Status

### Pod Status
```bash
NAME                                    READY   STATUS    RESTARTS   AGE
meeting-app-5fbf56c4bb-dj7g6            1/1     Running   0          21m
meeting-app-frontend-748997b8c6-scp2p   1/1     Running   0          93s
redis-75d4df6f48-lc6dk                  1/1     Running   0          21m
```

### Service Configuration
```bash
NAME                            TYPE        CLUSTER-IP       PORT(S)
meeting-app-frontend-external   NodePort    10.103.233.2    3000:30000/TCP
```

### Port Forwarding Status
```bash
Forwarding from 127.0.0.1:8080 -> 3000
Forwarding from [::1]:8080 -> 3000
```

## Access Points
The application can now be accessed through:
1. `http://localhost:8080/login` (via port forwarding)
2. `http://192.168.49.2:30000/login` (via Minikube IP)

## Lessons Learned
1. Always ensure proper configuration of path aliases in Next.js projects
2. Check for port conflicts when setting up port forwarding
3. Verify that context providers are properly set up in Next.js applications
4. Monitor pod logs and status for real-time debugging information

## Troubleshooting Steps for Future Reference

1. **Check Pod Status**
   ```bash
   kubectl get pods
   ```

2. **Check Service Status**
   ```bash
   kubectl get services
   ```

3. **View Pod Logs**
   ```bash
   kubectl logs -l app=meeting-app-frontend
   ```

4. **Port Forward Setup**
   ```bash
   kubectl port-forward service/meeting-app-frontend-external 8080:3000
   ```

5. **Get Minikube IP**
   ```bash
   minikube ip
   ```

## Maintenance Notes
- Keep the port forwarding terminal window open while accessing the application
- Monitor the pod logs for any new errors or issues
- Ensure all Kubernetes resources are properly configured before deploying updates 