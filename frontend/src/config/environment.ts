/**
 * Centralized environment configuration.
 * This module provides consistent access to environment variables
 * and validates their presence at runtime.
 */

import runtimeConfig from '../utils/runtimeConfig';

// Required environment variables that must be defined
interface RequiredEnvVars {
  // API URLs
  NEXT_PUBLIC_API_URL: string;
  NEXT_PUBLIC_AUTH_URL: string;
  NEXT_PUBLIC_WS_URL: string;
  
  // Other required configs
  NEXT_PUBLIC_APP_NAME: string;
  NEXT_PUBLIC_APP_VERSION: string;
}

// Optional environment variables with defaults
interface OptionalEnvVars {
  // Feature flags
  NEXT_PUBLIC_ENABLE_ANALYTICS: boolean;
  NEXT_PUBLIC_ENABLE_DEBUG_TOOLS: boolean;
  
  // Timeouts and limits
  NEXT_PUBLIC_API_TIMEOUT_MS: number;
  NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS: number;
  NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB: number;
}

// Environment configuration type
export type EnvConfig = RequiredEnvVars & OptionalEnvVars;

/**
 * Get environment variable with type checking - now using runtimeConfig instead of process.env
 */
function getEnvVar<T>(key: string, defaultValue?: T, parser?: (value: string) => T): T {
  // Use runtimeConfig as the primary source instead of process.env
  const value = runtimeConfig[key];
  
  // Handle undefined values
  if (value === undefined) {
    if (defaultValue !== undefined) {
      return defaultValue;
    }
    console.error(`Environment variable ${key} is not defined in runtimeConfig`);
    // Return a dummy value to prevent crashes
    return ('http://localhost:5000' as unknown) as T;
  }
  
  // Parse value if parser is provided
  if (parser && typeof value === 'string') {
    try {
      return parser(value);
    } catch (error) {
      console.error(`Failed to parse environment variable ${key}:`, error);
      if (defaultValue !== undefined) {
        return defaultValue;
      }
      throw new Error(`Failed to parse environment variable ${key}`);
    }
  }
  
  // Return value as is
  return value as unknown as T;
}

/**
 * Boolean parser for environment variables
 */
function parseBoolean(value: string): boolean {
  return value.toLowerCase() === 'true';
}

/**
 * Number parser for environment variables
 */
function parseNumber(value: string): number {
  const parsed = Number(value);
  if (isNaN(parsed)) {
    throw new Error(`Value "${value}" cannot be parsed as a number`);
  }
  return parsed;
}

/**
 * Environment configuration
 */
export const env: EnvConfig = {
  // Required environment variables
  NEXT_PUBLIC_API_URL: getEnvVar('NEXT_PUBLIC_API_URL'),
  NEXT_PUBLIC_AUTH_URL: getEnvVar('NEXT_PUBLIC_AUTH_URL'),
  NEXT_PUBLIC_WS_URL: getEnvVar('NEXT_PUBLIC_WS_URL'),
  NEXT_PUBLIC_APP_NAME: getEnvVar('NEXT_PUBLIC_APP_NAME'),
  NEXT_PUBLIC_APP_VERSION: getEnvVar('NEXT_PUBLIC_APP_VERSION'),
  
  // Optional environment variables with defaults
  NEXT_PUBLIC_ENABLE_ANALYTICS: getEnvVar('NEXT_PUBLIC_ENABLE_ANALYTICS', false, parseBoolean),
  NEXT_PUBLIC_ENABLE_DEBUG_TOOLS: getEnvVar('NEXT_PUBLIC_ENABLE_DEBUG_TOOLS', true, parseBoolean),
  NEXT_PUBLIC_API_TIMEOUT_MS: getEnvVar('NEXT_PUBLIC_API_TIMEOUT_MS', 30000, parseNumber),
  NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS: getEnvVar('NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS', 5000, parseNumber),
  NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB: getEnvVar('NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB', 5, parseNumber),
};

/**
 * Check if running in development mode
 */
export const isDevelopment = process.env.NODE_ENV === 'development';

/**
 * Check if running in production mode
 */
export const isProduction = process.env.NODE_ENV === 'production';

/**
 * Check if running in test mode
 */
export const isTest = process.env.NODE_ENV === 'test';

/**
 * Get base URL for the current environment
 */
export function getBaseUrl(): string {
  if (typeof window !== 'undefined') {
    return window.location.origin;
  }
  return runtimeConfig.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
}

export default env; 