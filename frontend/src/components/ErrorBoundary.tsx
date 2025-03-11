import React, { Component, ErrorInfo, ReactNode } from 'react';
import logger from '@/utils/logger';
import { isDevelopment } from '@/config/environment';

interface Props {
  children: ReactNode;
  fallback?: ReactNode | ((error: Error, errorInfo: ErrorInfo) => ReactNode);
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

/**
 * Error boundary component to catch JavaScript errors in child component tree.
 * Displays a fallback UI instead of crashing the whole app.
 */
class ErrorBoundary extends Component<Props, State> {
  readonly state: State = { hasError: false };
  readonly props!: Props;

  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Capture the error details
    this.setState({ errorInfo });
    
    // Log the error
    logger.error('Error caught by ErrorBoundary:', error);
    logger.error('Component stack:', errorInfo.componentStack);
    
    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    
    // In development, log to console for easier debugging
    if (isDevelopment) {
      console.error('Error caught by ErrorBoundary:', error);
      console.error('Component stack:', errorInfo.componentStack);
    }
  }

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback } = this.props;

    if (hasError && error) {
      // Check for custom fallback render function
      if (typeof fallback === 'function' && errorInfo) {
        return fallback(error, errorInfo);
      }
      
      // Use provided fallback component
      if (fallback && typeof fallback !== 'function') {
        return fallback;
      }
      
      // Default fallback UI
      return (
        <div className="error-boundary">
          <div className="error-container">
            <h2>Something went wrong</h2>
            <p className="error-message">{error.message}</p>
            {isDevelopment && errorInfo && (
              <details className="error-details">
                <summary>Component Stack</summary>
                <pre>{errorInfo.componentStack}</pre>
              </details>
            )}
            <button
              className="error-reset-button"
              onClick={() => this.setState({ hasError: false, error: undefined, errorInfo: undefined })}
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    // When there's no error, render children normally
    return children;
  }
}

/**
 * Higher-order component that wraps a component with an ErrorBoundary
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const displayName = Component.displayName || Component.name || 'Component';
  
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  WrappedComponent.displayName = `withErrorBoundary(${displayName})`;
  
  return WrappedComponent;
}

export default ErrorBoundary; 