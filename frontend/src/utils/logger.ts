/**
 * Logger utility for consistent logging across the application.
 * Provides different log levels and structured log format.
 */

import { env, isDevelopment } from '@/config/environment';

// Log levels
export enum LogLevel {
  TRACE = 0,
  DEBUG = 1,
  INFO = 2,
  WARN = 3,
  ERROR = 4,
  NONE = 5,
}

// Logger configuration
interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  prefix?: string;
  includeTimestamp: boolean;
}

// Default configuration
const defaultConfig: LoggerConfig = {
  level: isDevelopment ? LogLevel.DEBUG : LogLevel.INFO,
  enableConsole: true,
  includeTimestamp: true,
};

// Current logger configuration
let currentConfig: LoggerConfig = { ...defaultConfig };

/**
 * Set logger configuration
 */
export function configureLogger(config: Partial<LoggerConfig>): void {
  currentConfig = { ...currentConfig, ...config };
}

/**
 * Format log message with timestamp and prefix
 */
function formatLogMessage(message: string, level: string): string {
  const parts: string[] = [];
  
  // Add timestamp
  if (currentConfig.includeTimestamp) {
    parts.push(`[${new Date().toISOString()}]`);
  }
  
  // Add log level
  parts.push(`[${level}]`);
  
  // Add prefix if available
  if (currentConfig.prefix) {
    parts.push(`[${currentConfig.prefix}]`);
  }
  
  // Add message
  parts.push(message);
  
  return parts.join(' ');
}

/**
 * Create console method with structured format
 */
function createLogMethod(
  level: LogLevel,
  methodName: 'log' | 'info' | 'debug' | 'warn' | 'error',
  levelName: string
) {
  return function(...args: any[]): void {
    // Skip if log level is too low
    if (level < currentConfig.level) {
      return;
    }
    
    // Skip if console logging is disabled
    if (!currentConfig.enableConsole) {
      return;
    }
    
    // Get message
    const message = args.map(arg => {
      if (typeof arg === 'object') {
        try {
          return JSON.stringify(arg);
        } catch (e) {
          return String(arg);
        }
      }
      return String(arg);
    }).join(' ');
    
    // Format message
    const formattedMessage = formatLogMessage(message, levelName);
    
    // Log to console
    console[methodName](formattedMessage);
    
    // Send to remote logging service if in production
    if (!isDevelopment && level >= LogLevel.ERROR) {
      // Here you would integrate with a service like Sentry
      // if (typeof window !== 'undefined' && window.Sentry) {
      //   window.Sentry.captureMessage(message, levelName.toLowerCase());
      // }
    }
  };
}

/**
 * Create debug context with custom prefix
 */
export function createLogger(prefix: string): Logger {
  return {
    trace: (...args: any[]) => {
      const prevPrefix = currentConfig.prefix;
      currentConfig.prefix = prefix;
      trace(...args);
      currentConfig.prefix = prevPrefix;
    },
    debug: (...args: any[]) => {
      const prevPrefix = currentConfig.prefix;
      currentConfig.prefix = prefix;
      debug(...args);
      currentConfig.prefix = prevPrefix;
    },
    info: (...args: any[]) => {
      const prevPrefix = currentConfig.prefix;
      currentConfig.prefix = prefix;
      info(...args);
      currentConfig.prefix = prevPrefix;
    },
    warn: (...args: any[]) => {
      const prevPrefix = currentConfig.prefix;
      currentConfig.prefix = prefix;
      warn(...args);
      currentConfig.prefix = prevPrefix;
    },
    error: (...args: any[]) => {
      const prevPrefix = currentConfig.prefix;
      currentConfig.prefix = prefix;
      error(...args);
      currentConfig.prefix = prevPrefix;
    },
  };
}

// Logger interface
export interface Logger {
  trace: (...args: any[]) => void;
  debug: (...args: any[]) => void;
  info: (...args: any[]) => void;
  warn: (...args: any[]) => void;
  error: (...args: any[]) => void;
}

// Create log methods
export const trace = createLogMethod(LogLevel.TRACE, 'debug', 'TRACE');
export const debug = createLogMethod(LogLevel.DEBUG, 'debug', 'DEBUG');
export const info = createLogMethod(LogLevel.INFO, 'info', 'INFO');
export const warn = createLogMethod(LogLevel.WARN, 'warn', 'WARN');
export const error = createLogMethod(LogLevel.ERROR, 'error', 'ERROR');

// Default logger
const logger: Logger = {
  trace,
  debug,
  info,
  warn,
  error,
};

// Initialize logger
if (typeof window !== 'undefined') {
  // Set log level from URL params for debugging
  const params = new URLSearchParams(window.location.search);
  const logLevel = params.get('log_level');
  if (logLevel) {
    const level = parseInt(logLevel, 10);
    if (!isNaN(level) && level >= 0 && level <= 5) {
      configureLogger({ level: level as LogLevel });
      debug(`Log level set to ${LogLevel[level]}`);
    }
  }
  
  // Log app initialization
  info(
    `App initialized: ${env.NEXT_PUBLIC_APP_NAME} ${env.NEXT_PUBLIC_APP_VERSION} - ${window.location.href}`
  );
}

export default logger; 