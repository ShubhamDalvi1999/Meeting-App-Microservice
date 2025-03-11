import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { env, isDevelopment } from '@/config/environment';
import logger, { LogLevel, configureLogger } from '@/utils/logger';
import { getPendingRequests, abortAllRequests } from '@/services/api/client';

// Debug context state
interface DebugContextState {
  isDebugEnabled: boolean;
  toggleDebug: () => void;
  logLevel: LogLevel;
  setLogLevel: (level: LogLevel) => void;
  lastApiResponses: Array<{
    url: string;
    method: string;
    status: number;
    timestamp: number;
    duration: number;
  }>;
  pendingRequests: Array<{
    url: string;
    method: string;
    timestamp: number;
    duration: number;
  }>;
  appState: Record<string, any>;
  captureState: (key: string, value: any) => void;
  clearState: (key?: string) => void;
  abortAllRequests: () => void;
}

// Default context value
const defaultContext: DebugContextState = {
  isDebugEnabled: false,
  toggleDebug: () => {},
  logLevel: LogLevel.INFO,
  setLogLevel: () => {},
  lastApiResponses: [],
  pendingRequests: [],
  appState: {},
  captureState: () => {},
  clearState: () => {},
  abortAllRequests: () => {},
};

// Create context
const DebugContext = createContext<DebugContextState>(defaultContext);

// Maximum number of API responses to store
const MAX_API_RESPONSES = 100;

/**
 * Debug context provider component
 */
export const DebugProvider: React.FC<{
  children: React.ReactNode;
  initialEnabled?: boolean | string;
}> = ({ children, initialEnabled = env.NEXT_PUBLIC_ENABLE_DEBUG_TOOLS }) => {
  // Debug state
  const [isDebugEnabled, setIsDebugEnabled] = useState<boolean>(
    isDevelopment && (initialEnabled === true || initialEnabled === 'true')
  );
  
  // Log level state
  const [logLevel, setLogLevelState] = useState<LogLevel>(
    isDevelopment ? LogLevel.DEBUG : LogLevel.INFO
  );
  
  // API history state
  const [lastApiResponses, setLastApiResponses] = useState<Array<{
    url: string;
    method: string;
    status: number;
    timestamp: number;
    duration: number;
  }>>([]);
  
  // App state capture
  const [appState, setAppState] = useState<Record<string, any>>({});
  
  // Toggle debug mode
  const toggleDebug = useCallback(() => {
    setIsDebugEnabled(prev => !prev);
  }, []);
  
  // Set log level
  const setLogLevel = useCallback((level: LogLevel) => {
    setLogLevelState(level);
    configureLogger({ level });
    
    // Log the change
    logger.info(`Log level set to ${LogLevel[level]}`);
  }, []);
  
  // Capture application state for debugging
  const captureState = useCallback((key: string, value: any) => {
    setAppState(prev => ({
      ...prev,
      [key]: value,
      _lastUpdated: Date.now(),
    }));
  }, []);
  
  // Clear captured state
  const clearState = useCallback((key?: string) => {
    if (key) {
      setAppState(prev => {
        const newState = { ...prev };
        delete newState[key];
        return {
          ...newState,
          _lastUpdated: Date.now(),
        };
      });
    } else {
      setAppState({ _lastUpdated: Date.now() });
    }
  }, []);
  
  // Get pending requests
  const [pendingRequests, setPendingRequests] = useState<Array<{
    url: string;
    method: string;
    timestamp: number;
    duration: number;
  }>>([]);
  
  // Register API response listener
  useEffect(() => {
    if (!isDebugEnabled || !isDevelopment) {
      return;
    }
    
    // Register event listener for API responses
    const handleApiResponse = (event: CustomEvent) => {
      const { url, method, status, timestamp, duration } = event.detail;
      
      setLastApiResponses(prev => {
        const newResponses = [
          { url, method, status, timestamp, duration },
          ...prev,
        ].slice(0, MAX_API_RESPONSES);
        
        return newResponses;
      });
    };
    
    // Create custom event for API responses
    window.addEventListener('api-response', handleApiResponse as EventListener);
    
    // Clean up
    return () => {
      window.removeEventListener('api-response', handleApiResponse as EventListener);
    };
  }, [isDebugEnabled]);
  
  // Register keyboard shortcut for debug mode
  useEffect(() => {
    if (!isDevelopment) {
      return;
    }
    
    // Toggle debug mode with Ctrl+Shift+D
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.shiftKey && event.key === 'D') {
        toggleDebug();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    
    // Clean up
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [toggleDebug]);
  
  // Update pending requests
  useEffect(() => {
    if (!isDebugEnabled || !isDevelopment) {
      return;
    }
    
    // Poll for pending requests
    const intervalId = setInterval(() => {
      const requests = getPendingRequests();
      const now = Date.now();
      
      setPendingRequests(
        requests.map(req => ({
          url: req.url,
          method: req.method,
          timestamp: req.timestamp,
          duration: now - req.timestamp,
        }))
      );
    }, 100);
    
    // Clean up
    return () => {
      clearInterval(intervalId);
    };
  }, [isDebugEnabled]);
  
  // Set initial log level
  useEffect(() => {
    configureLogger({ level: logLevel });
  }, [logLevel]);
  
  // Context value
  const contextValue: DebugContextState = {
    isDebugEnabled,
    toggleDebug,
    logLevel,
    setLogLevel,
    lastApiResponses,
    pendingRequests,
    appState,
    captureState,
    clearState,
    abortAllRequests,
  };
  
  return (
    <DebugContext.Provider value={contextValue}>
      {children}
      {isDebugEnabled && isDevelopment && (
        <DebugOverlay />
      )}
    </DebugContext.Provider>
  );
};

/**
 * Debug overlay component
 * Shown when debug mode is enabled
 */
const DebugOverlay: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const { logLevel, setLogLevel, lastApiResponses, pendingRequests, appState } = useContext(DebugContext);
  
  // Toggle expanded state
  const toggleExpanded = () => {
    setIsExpanded(prev => !prev);
  };
  
  // Format date
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };
  
  // Handle log level change
  const handleLogLevelChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setLogLevel(Number(event.target.value) as LogLevel);
  };
  
  // Minimize style
  if (!isExpanded) {
    return (
      <div className="debug-overlay-minimized">
        <button onClick={toggleExpanded}>📊 Debug</button>
      </div>
    );
  }
  
  // Full debug overlay
  return (
    <div className="debug-overlay">
      <div className="debug-header">
        <h3>Debug Tools</h3>
        <button onClick={toggleExpanded}>Minimize</button>
      </div>
      
      <div className="debug-content">
        <div className="debug-section">
          <h4>Settings</h4>
          <div className="debug-setting">
            <label htmlFor="logLevel">Log Level:</label>
            <select 
              id="logLevel" 
              value={logLevel} 
              onChange={handleLogLevelChange}
            >
              <option value={LogLevel.TRACE}>Trace</option>
              <option value={LogLevel.DEBUG}>Debug</option>
              <option value={LogLevel.INFO}>Info</option>
              <option value={LogLevel.WARN}>Warning</option>
              <option value={LogLevel.ERROR}>Error</option>
              <option value={LogLevel.NONE}>None</option>
            </select>
          </div>
        </div>
        
        <div className="debug-section">
          <h4>Pending Requests ({pendingRequests.length})</h4>
          <div className="debug-requests">
            {pendingRequests.length === 0 ? (
              <p>No pending requests</p>
            ) : (
              <ul>
                {pendingRequests.map((request, index) => (
                  <li key={index}>
                    {request.method} {request.url} 
                    ({request.duration}ms, started at {formatTime(request.timestamp)})
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        
        <div className="debug-section">
          <h4>Recent API Responses</h4>
          <div className="debug-responses">
            {lastApiResponses.length === 0 ? (
              <p>No API responses yet</p>
            ) : (
              <ul>
                {lastApiResponses.slice(0, 5).map((response, index) => (
                  <li key={index} className={response.status >= 400 ? 'error' : 'success'}>
                    {response.method} {response.url} 
                    ({response.status}, {response.duration}ms, at {formatTime(response.timestamp)})
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        
        <div className="debug-section">
          <h4>Captured State</h4>
          <div className="debug-state">
            <pre>{JSON.stringify(appState, null, 2)}</pre>
          </div>
        </div>
      </div>
      
      <style jsx>{`
        .debug-overlay {
          position: fixed;
          bottom: 0;
          right: 0;
          width: 400px;
          max-height: 50vh;
          background-color: rgba(0, 0, 0, 0.8);
          color: white;
          border-top-left-radius: 8px;
          overflow: auto;
          z-index: 9999;
          font-family: monospace;
          font-size: 12px;
        }
        
        .debug-overlay-minimized {
          position: fixed;
          bottom: 10px;
          right: 10px;
          z-index: 9999;
        }
        
        .debug-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px;
          background-color: #333;
          border-bottom: 1px solid #555;
        }
        
        .debug-content {
          padding: 8px;
        }
        
        .debug-section {
          margin-bottom: 16px;
        }
        
        .debug-section h4 {
          margin-top: 0;
          margin-bottom: 8px;
          border-bottom: 1px solid #555;
        }
        
        .debug-requests, .debug-responses, .debug-state {
          max-height: 200px;
          overflow: auto;
        }
        
        ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        
        li {
          padding: 4px 0;
          border-bottom: 1px solid #444;
        }
        
        li.error {
          color: #ff6b6b;
        }
        
        li.success {
          color: #69db7c;
        }
        
        .debug-setting {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
        }
        
        .debug-setting label {
          margin-right: 8px;
        }
        
        button {
          background-color: #555;
          color: white;
          border: none;
          padding: 4px 8px;
          border-radius: 4px;
          cursor: pointer;
        }
        
        button:hover {
          background-color: #777;
        }
        
        pre {
          margin: 0;
          white-space: pre-wrap;
        }
      `}</style>
    </div>
  );
};

/**
 * Debug context hook
 */
export const useDebug = () => useContext(DebugContext);

export default DebugContext; 