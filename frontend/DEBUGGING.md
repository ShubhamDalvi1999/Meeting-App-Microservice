# Frontend Debugging Guide

This document provides guidance on debugging the Next.js frontend application.

## Environment Setup

Before you begin, ensure that you have the correct environment variables set up. The application uses the following environment variables:

```
# Required environment variables
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_AUTH_URL=http://localhost:5001
NEXT_PUBLIC_WS_URL=ws://localhost:3001
NEXT_PUBLIC_APP_NAME=Meeting App
NEXT_PUBLIC_APP_VERSION=1.0.0

# Optional environment variables
NEXT_PUBLIC_ENABLE_DEBUG_TOOLS=true  # Enable debug tools (default: true in development, false in production)
NEXT_PUBLIC_ENABLE_ANALYTICS=false   # Enable analytics (default: false)
```

## Debugging Tools

### Built-in Debug Overlay

The application includes a built-in debug overlay that can be toggled by pressing `Ctrl+Shift+D` in development mode. The debug overlay provides:

- Current log level control
- Pending API requests
- Recent API responses
- Application state capture

### URL Parameters

You can control certain aspects of the application by adding query parameters to the URL:

- `?log_level=1` - Set log level (0=TRACE, 1=DEBUG, 2=INFO, 3=WARN, 4=ERROR, 5=NONE)
- `?debug=true` - Force enable debug mode

### Console Logging

The application uses a structured logging system with different log levels:

```typescript
import logger from '@/utils/logger';

// Different log levels
logger.trace('Detailed trace information');
logger.debug('Debugging information');
logger.info('General information');
logger.warn('Warning message');
logger.error('Error message');

// Logging with context
const componentLogger = createLogger('ComponentName');
componentLogger.info('Component initialized');
```

## Browser DevTools

### React Developer Tools

Install the [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi) extension for Chrome or Firefox to inspect component props, state, and hierarchy.

### Network Tab

The Network tab in browser DevTools is essential for debugging API requests:

1. Open DevTools (F12 or Ctrl+Shift+I)
2. Go to the Network tab
3. Filter by "Fetch/XHR" to see only API requests
4. Look for the `X-Request-ID` header in requests to correlate with backend logs

### Debugging API Requests

All API requests include a unique `X-Request-ID` header that can be used to trace requests from the frontend to the backend.

Example of manually inspecting an API request:

```typescript
// Get a reference to the API client
import { apiClient } from '@/services/api/client';

// Make a request
const response = await apiClient.get('/api/meetings');

// Check response
console.log('Response:', response);

// If there was an error
if (response.error) {
  console.error('Error:', response.error);
}
```

## Error Handling

### Error Boundaries

The application uses React Error Boundaries to catch and display errors gracefully. You can wrap specific components with an error boundary for more granular error handling:

```typescript
import ErrorBoundary from '@/components/ErrorBoundary';

// In your component
return (
  <ErrorBoundary
    fallback={<div>Something went wrong with this component</div>}
    onError={(error) => console.error('Component error:', error)}
  >
    <YourComponent />
  </ErrorBoundary>
);
```

### Debugging Production Errors

For production debugging, check the browser console for error messages. All unhandled errors are logged and could be sent to an error tracking service.

## Debugging Specific Issues

### State Management Issues

Use the Debug Context to capture and inspect application state:

```typescript
import { useDebug } from '@/contexts/DebugContext';

function YourComponent() {
  const { captureState } = useDebug();
  
  // Capture state for debugging
  useEffect(() => {
    captureState('componentState', { 
      // Your component state here
    });
  }, [captureState, /* your dependencies */]);
  
  // ...
}
```

### Performance Issues

Use the `why-did-you-render` package to track unnecessary re-renders:

```typescript
// In your component file
import React from 'react';

if (process.env.NODE_ENV === 'development') {
  YourComponent.whyDidYouRender = true;
}

// Or enable globally for specific components in _app.tsx
```

### WebSocket Debugging

For WebSocket connection issues:

1. Check the browser console for connection errors
2. Verify the NEXT_PUBLIC_WS_URL environment variable
3. Use the Network tab in DevTools, filter by "WS" to see WebSocket connections
4. Look for the `X-Request-ID` and `X-Correlation-ID` headers in the initial WebSocket handshake

## Running in Debug Mode

To run the application with Node.js inspector for step-by-step debugging:

```bash
npm run start:debug
```

Then connect your IDE's debugger or open Chrome DevTools and navigate to chrome://inspect.

## Bundle Analysis

To analyze the bundle size:

```bash
npm run analyze
```

This will generate a report showing the size of each bundle and help identify large dependencies.

## TypeScript Type Checking

Run TypeScript type checking:

```bash
npx tsc --noEmit
```

## Common Issues and Solutions

1. **API Requests Failing**
   - Check network tab for status codes
   - Verify API URL environment variable
   - Check CORS settings
   - Look for authentication issues (expired tokens)

2. **Component Not Rendering**
   - Check if it's wrapped in a conditional that evaluates to false
   - Verify that parent components are rendering
   - Check for errors in the console

3. **Slow Performance**
   - Use React DevTools Profiler to identify slow components
   - Look for unnecessary re-renders
   - Check for expensive operations in render functions
   - Verify that proper memoization is used (useMemo, useCallback)

4. **Authentication Issues**
   - Check local storage for token expiration
   - Verify that tokens are being sent with requests
   - Look for CORS issues with credentials

## Useful Debugging Commands

```javascript
// In browser console

// Get current environment config
console.log(window.__NEXT_DATA__.props.pageProps.env);

// Get app state
console.log(window.__APP_STATE__);

// Force garbage collection (Chrome only, requires --enable-precise-memory-info flag)
window.gc();

// Check for memory leaks
performance.memory;

// Monitor events on an element
monitorEvents(document.querySelector('#your-element-id'));
``` 