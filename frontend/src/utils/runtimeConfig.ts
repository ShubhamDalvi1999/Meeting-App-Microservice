/**
 * Runtime configuration for client-side environment variables.
 * This approach ensures environment variables are available in the browser.
 */

export interface RuntimeConfig {
  // API URLs
  NEXT_PUBLIC_API_URL: string;
  NEXT_PUBLIC_AUTH_URL: string;
  NEXT_PUBLIC_WS_URL: string;
  NEXT_PUBLIC_BASE_URL: string;
  
  // App information
  NEXT_PUBLIC_APP_NAME: string;
  NEXT_PUBLIC_APP_VERSION: string;
  
  // Feature flags
  NEXT_PUBLIC_ENABLE_ANALYTICS: boolean;
  NEXT_PUBLIC_ENABLE_DEBUG_TOOLS: boolean;
  
  // Timeouts and limits
  NEXT_PUBLIC_API_TIMEOUT_MS: number;
  NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS: number;
  NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB: number;
  
  // OAuth
  NEXT_PUBLIC_GOOGLE_CLIENT_ID: string;
  
  // Allow indexing with string
  [key: string]: string | number | boolean;
}

// HARDCODED VALUES FOR GUARANTEED ACCESS
const runtimeConfig: RuntimeConfig = {
  // API URLs
  NEXT_PUBLIC_API_URL: 'http://localhost:5000',
  NEXT_PUBLIC_AUTH_URL: 'http://localhost:5001',
  NEXT_PUBLIC_WS_URL: 'ws://localhost:3001',
  NEXT_PUBLIC_BASE_URL: 'http://localhost:3000',
  
  // App information
  NEXT_PUBLIC_APP_NAME: 'Meeting App',
  NEXT_PUBLIC_APP_VERSION: '1.0.0',
  
  // Feature flags
  NEXT_PUBLIC_ENABLE_ANALYTICS: false,
  NEXT_PUBLIC_ENABLE_DEBUG_TOOLS: false,
  
  // Timeouts and limits
  NEXT_PUBLIC_API_TIMEOUT_MS: 30000,
  NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS: 5000,
  NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB: 5,
  
  // OAuth
  NEXT_PUBLIC_GOOGLE_CLIENT_ID: '1004556025731-dgnou2c5vdui47ffbfievlil9ncqsrue.apps.googleusercontent.com',
};

// We're not going to try to override with window values for now
// Just use the hardcoded values

export default runtimeConfig; 