/**
 * API client with interceptors for debugging and error tracking.
 * Provides a standardized way to make API requests with automatic error handling.
 */

import { env, isDevelopment } from '@/config/environment';
import logger from '@/utils/logger';

// Request options type
export interface ApiRequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  timeout?: number;
}

// Response type
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Headers;
  error?: Error;
}

// Request tracking
interface PendingRequest {
  timestamp: number;
  url: string;
  method: string;
  abortController: AbortController;
}

// Global request tracking for debugging
const pendingRequests: PendingRequest[] = [];

/**
 * Creates a query string from params object
 */
function createQueryString(params?: Record<string, string | number | boolean | undefined>): string {
  if (!params) return '';
  
  const queryParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      queryParams.append(key, String(value));
    }
  });
  
  const queryString = queryParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * Adds request ID header to requests
 */
function addRequestId(headers: Headers): Headers {
  // Generate a unique request ID if not already present
  if (!headers.has('X-Request-ID')) {
    headers.set('X-Request-ID', `frontend-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`);
  }
  
  return headers;
}

/**
 * Formats the API URL based on the environment
 */
function formatUrl(path: string): string {
  // If the path is already a full URL, return it as is
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  
  // Remove leading slash if present
  const cleanPath = path.startsWith('/') ? path.substring(1) : path;
  
  // Combine API URL with path
  return `${env.NEXT_PUBLIC_API_URL}/${cleanPath}`;
}

/**
 * Fetch API with timeout and automatic error handling
 */
async function fetchWithTimeout(
  url: string, 
  options: ApiRequestOptions = {}
): Promise<Response> {
  const { timeout = env.NEXT_PUBLIC_API_TIMEOUT_MS, ...fetchOptions } = options;
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const signal = controller.signal;
  
  // Set up timeout
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeout);
  
  try {
    // Track request for debugging
    const pendingRequest: PendingRequest = {
      timestamp: Date.now(),
      url,
      method: options.method || 'GET',
      abortController: controller
    };
    
    pendingRequests.push(pendingRequest);
    
    // Make the request
    const response = await fetch(url, {
      ...fetchOptions,
      signal,
    });
    
    return response;
  } finally {
    // Clean up timeout and pending request
    clearTimeout(timeoutId);
    
    // Remove from pending requests
    const index = pendingRequests.findIndex(req => 
      req.url === url && req.abortController === controller
    );
    
    if (index !== -1) {
      pendingRequests.splice(index, 1);
    }
  }
}

/**
 * Make an API request with standardized error handling and logging
 */
export async function apiRequest<T = any>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const startTime = performance.now();
  
  // Create a headers object to extract request ID if present
  const headersObj = new Headers(options.headers || {});
  const requestId = headersObj.get('X-Request-ID') || `req-${Date.now()}`;
  
  // Prepare request
  const { params, ...fetchOptions } = options;
  
  // Create URL with query parameters
  const queryString = createQueryString(params);
  const url = `${formatUrl(path)}${queryString}`;
  
  // Prepare headers with request ID
  const headers = new Headers(options.headers || {});
  addRequestId(headers);
  
  // Log request in development
  if (isDevelopment) {
    logger.debug(`API Request [${requestId}]: ${options.method || 'GET'} ${url}`);
    if (options.body) {
      try {
        let bodyContent = options.body;
        if (typeof bodyContent === 'string') {
          bodyContent = JSON.parse(bodyContent);
        }
        logger.debug(`Request body [${requestId}]:`, bodyContent);
      } catch (e) {
        // Ignore parsing errors for non-JSON bodies
      }
    }
  }
  
  try {
    // Make the request
    const response = await fetchWithTimeout(url, {
      ...fetchOptions,
      headers,
    });
    
    // Parse response data (handle different content types)
    let data: T;
    const contentType = response.headers.get('content-type');
    
    if (contentType?.includes('application/json')) {
      data = await response.json();
    } else if (contentType?.includes('text/')) {
      data = await response.text() as unknown as T;
    } else {
      // Handle binary data or other formats
      data = await response.blob() as unknown as T;
    }
    
    // Calculate request time
    const endTime = performance.now();
    const requestTime = endTime - startTime;
    
    // Log response in development
    if (isDevelopment) {
      logger.debug(
        `API Response [${requestId}]: ${response.status} ${response.statusText} (${requestTime.toFixed(2)}ms)`
      );
      logger.debug(`Response data [${requestId}]:`, data);
    }
    
    // Check if response is an error
    if (!response.ok) {
      // Format error for consistent handling
      const error = new Error(
        `API Error ${response.status}: ${response.statusText}`
      );
      
      // Add response data to error object for more details
      Object.assign(error, { response, data });
      
      // Log error
      logger.error(`API Error [${requestId}]: ${response.status} ${url}`, error);
      
      return {
        data,
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        error,
      };
    }
    
    // Return successful response
    return {
      data,
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    };
  } catch (error) {
    // Handle fetch errors (network, timeout, etc.)
    const apiError = error instanceof Error ? error : new Error(String(error));
    
    // Log error
    logger.error(`API Request Failed [${requestId}]: ${url}`, apiError);
    
    // Return error response
    return {
      data: null as unknown as T,
      status: apiError.name === 'AbortError' ? 408 : 0,
      statusText: apiError.name === 'AbortError' ? 'Request Timeout' : 'Network Error',
      headers: new Headers(),
      error: apiError,
    };
  }
}

/**
 * Helper for GET requests
 */
export function get<T = any>(
  path: string, 
  options: Omit<ApiRequestOptions, 'method' | 'body'> = {}
): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, { ...options, method: 'GET' });
}

/**
 * Helper for POST requests
 */
export function post<T = any>(
  path: string, 
  data?: any, 
  options: Omit<ApiRequestOptions, 'method' | 'body'> = {}
): Promise<ApiResponse<T>> {
  const headers = new Headers(options.headers || {});
  if (data && !(data instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  return apiRequest<T>(path, {
    ...options,
    method: 'POST',
    headers,
    body: data instanceof FormData ? data : data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Helper for PUT requests
 */
export function put<T = any>(
  path: string, 
  data?: any, 
  options: Omit<ApiRequestOptions, 'method' | 'body'> = {}
): Promise<ApiResponse<T>> {
  const headers = new Headers(options.headers || {});
  if (data && !(data instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  return apiRequest<T>(path, {
    ...options,
    method: 'PUT',
    headers,
    body: data instanceof FormData ? data : data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Helper for DELETE requests
 */
export function del<T = any>(
  path: string, 
  options: Omit<ApiRequestOptions, 'method'> = {}
): Promise<ApiResponse<T>> {
  return apiRequest<T>(path, { ...options, method: 'DELETE' });
}

/**
 * Helper for PATCH requests
 */
export function patch<T = any>(
  path: string, 
  data?: any, 
  options: Omit<ApiRequestOptions, 'method' | 'body'> = {}
): Promise<ApiResponse<T>> {
  const headers = new Headers(options.headers || {});
  if (data && !(data instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  return apiRequest<T>(path, {
    ...options,
    method: 'PATCH',
    headers,
    body: data instanceof FormData ? data : data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Debug utility to get all pending requests
 */
export function getPendingRequests(): PendingRequest[] {
  return [...pendingRequests];
}

/**
 * Debug utility to abort all pending requests
 */
export function abortAllRequests(): void {
  pendingRequests.forEach(request => {
    request.abortController.abort();
  });
}

/**
 * Export API client with all methods
 */
export const apiClient = {
  request: apiRequest,
  get,
  post,
  put,
  delete: del,
  patch,
  getPendingRequests,
  abortAllRequests,
};

export default apiClient; 