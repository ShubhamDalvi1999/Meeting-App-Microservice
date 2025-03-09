/**
 * Global declarations for the application.
 * This file provides type definitions for globals that may not be properly recognized.
 */

// Declare process.env for TypeScript
declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test';
    NEXT_PUBLIC_API_URL: string;
    NEXT_PUBLIC_AUTH_URL: string;
    NEXT_PUBLIC_WS_URL: string;
    NEXT_PUBLIC_APP_NAME: string;
    NEXT_PUBLIC_APP_VERSION: string;
    NEXT_PUBLIC_ENABLE_ANALYTICS?: string;
    NEXT_PUBLIC_ENABLE_DEBUG_TOOLS?: string;
    NEXT_PUBLIC_API_TIMEOUT_MS?: string;
    NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS?: string;
    NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB?: string;
  }
}

// Make sure TypeScript knows process exists globally
declare const process: NodeJS.Process; 