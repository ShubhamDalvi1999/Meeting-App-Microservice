# 5. Error Handling

## Overview
This document covers comprehensive error handling strategies in our React application. These concepts are crucial for building a robust and user-friendly application.

## Error Types

### 1. Runtime Errors
Errors that occur during application execution:

```typescript
// types/errors.ts
export class ApplicationError extends Error {
    constructor(
        message: string,
        public code: string,
        public severity: 'low' | 'medium' | 'high'
    ) {
        super(message);
        this.name = 'ApplicationError';
    }
}

export class ValidationError extends ApplicationError {
    constructor(
        message: string,
        public fieldErrors: Record<string, string>
    ) {
        super(message, 'VALIDATION_ERROR', 'medium');
        this.name = 'ValidationError';
    }
}

export class NetworkError extends ApplicationError {
    constructor(message: string) {
        super(message, 'NETWORK_ERROR', 'high');
        this.name = 'NetworkError';
    }
}
```

### 2. API Errors
Handling errors from API responses:

```typescript
// utils/apiErrors.ts
export class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
        public data?: any
    ) {
        super(message);
        this.name = 'ApiError';
    }

    static fromResponse(error: unknown): ApiError {
        if (axios.isAxiosError(error)) {
            return new ApiError(
                error.response?.status || 500,
                error.response?.data?.message || 'An unexpected error occurred',
                error.response?.data
            );
        }
        return new ApiError(500, 'An unexpected error occurred');
    }

    get isNotFound() {
        return this.status === 404;
    }

    get isUnauthorized() {
        return this.status === 401;
    }

    get isForbidden() {
        return this.status === 403;
    }
}
```

## Error Boundaries

### 1. Global Error Boundary
```typescript
// components/error/GlobalErrorBoundary.tsx
interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class GlobalErrorBoundary extends React.Component<Props, State> {
    state: State = {
        hasError: false,
        error: null
    };

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error
        };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        // Log to error reporting service
        errorReportingService.log(error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <ErrorPage
                    error={this.state.error}
                    onReset={() => {
                        this.setState({ hasError: false, error: null });
                    }}
                />
            );
        }

        return this.props.children;
    }
}
```

### 2. Feature-Level Error Boundaries
```typescript
// components/error/FeatureErrorBoundary.tsx
interface Props {
    feature: string;
    fallback: ReactNode | ((error: Error) => ReactNode);
    children: ReactNode;
}

export class FeatureErrorBoundary extends React.Component<Props, State> {
    state: State = {
        hasError: false,
        error: null
    };

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            error
        };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        errorReportingService.log(error, errorInfo, {
            feature: this.props.feature
        });
    }

    render() {
        if (this.state.hasError) {
            return typeof this.props.fallback === 'function'
                ? this.props.fallback(this.state.error!)
                : this.props.fallback;
        }

        return this.props.children;
    }
}

// Usage
function MeetingsList() {
    return (
        <FeatureErrorBoundary
            feature="meetings-list"
            fallback={error => (
                <ErrorMessage
                    title="Failed to load meetings"
                    message={error.message}
                    action={<RetryButton />}
                />
            )}
        >
            <MeetingsContent />
        </FeatureErrorBoundary>
    );
}
```

## Error Handling Hooks

### 1. useErrorHandler
```typescript
// hooks/useErrorHandler.ts
interface ErrorHandlerOptions {
    showNotification?: boolean;
    reportToService?: boolean;
}

function useErrorHandler(options: ErrorHandlerOptions = {}) {
    const handleError = useCallback((error: unknown) => {
        const processedError = processError(error);

        if (options.showNotification) {
            showErrorNotification(processedError);
        }

        if (options.reportToService) {
            errorReportingService.log(processedError);
        }

        return processedError;
    }, [options.showNotification, options.reportToService]);

    return handleError;
}

// Usage
function MeetingForm() {
    const handleError = useErrorHandler({
        showNotification: true,
        reportToService: true
    });

    const onSubmit = async (data: MeetingFormData) => {
        try {
            await submitMeeting(data);
        } catch (error) {
            const processedError = handleError(error);
            if (processedError instanceof ValidationError) {
                setFieldErrors(processedError.fieldErrors);
            }
        }
    };
}
```

### 2. useAsyncError
```typescript
// hooks/useAsyncError.ts
function useAsyncError<T>(
    asyncFn: () => Promise<T>,
    options: {
        onError?: (error: Error) => void;
        retry?: boolean;
    } = {}
) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const [data, setData] = useState<T | null>(null);

    const execute = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const result = await asyncFn();
            setData(result);
            return result;
        } catch (err) {
            const error = err instanceof Error ? err : new Error('Unknown error');
            setError(error);
            options.onError?.(error);
            throw error;
        } finally {
            setLoading(false);
        }
    }, [asyncFn, options.onError]);

    return {
        execute,
        loading,
        error,
        data,
        retry: options.retry ? execute : undefined
    };
}

// Usage
function MeetingDetails({ id }: { id: number }) {
    const {
        execute: fetchMeeting,
        loading,
        error,
        data: meeting,
        retry
    } = useAsyncError(
        () => api.meetings.getById(id),
        {
            onError: (error) => {
                if (error instanceof ApiError && error.isNotFound) {
                    navigate('/meetings');
                }
            },
            retry: true
        }
    );

    useEffect(() => {
        fetchMeeting();
    }, [fetchMeeting]);

    if (error) {
        return (
            <ErrorMessage
                message={error.message}
                action={retry && <RetryButton onClick={retry} />}
            />
        );
    }

    return <MeetingContent meeting={meeting} />;
}
```

## Error UI Components

### 1. Error Messages
```typescript
// components/error/ErrorMessage.tsx
interface ErrorMessageProps {
    title?: string;
    message: string;
    action?: ReactNode;
    variant?: 'inline' | 'full';
}

function ErrorMessage({
    title,
    message,
    action,
    variant = 'inline'
}: ErrorMessageProps) {
    return (
        <div className={`error-message error-message-${variant}`}>
            {title && <h3 className="error-title">{title}</h3>}
            <p className="error-text">{message}</p>
            {action && <div className="error-action">{action}</div>}
        </div>
    );
}
```

### 2. Error Pages
```typescript
// components/error/ErrorPage.tsx
interface ErrorPageProps {
    error: Error;
    onReset?: () => void;
}

function ErrorPage({ error, onReset }: ErrorPageProps) {
    const isNetworkError = error instanceof NetworkError;
    const isNotFound = error instanceof ApiError && error.isNotFound;

    return (
        <div className="error-page">
            <div className="error-content">
                <ErrorIcon type={isNetworkError ? 'network' : 'generic'} />
                <h1>
                    {isNetworkError
                        ? 'Connection Error'
                        : isNotFound
                        ? 'Page Not Found'
                        : 'Something Went Wrong'}
                </h1>
                <p>{error.message}</p>
                <div className="error-actions">
                    {onReset && (
                        <Button onClick={onReset}>
                            Try Again
                        </Button>
                    )}
                    <Button onClick={() => navigate('/')}>
                        Go to Home
                    </Button>
                </div>
            </div>
        </div>
    );
}
```

## Error Reporting

### 1. Error Reporting Service
```typescript
// services/errorReporting.ts
interface ErrorReport {
    error: Error;
    errorInfo?: React.ErrorInfo;
    metadata?: Record<string, any>;
    timestamp: number;
}

class ErrorReportingService {
    private queue: ErrorReport[] = [];
    private isProcessing = false;

    async log(
        error: Error,
        errorInfo?: React.ErrorInfo,
        metadata?: Record<string, any>
    ) {
        this.queue.push({
            error,
            errorInfo,
            metadata,
            timestamp: Date.now()
        });

        if (!this.isProcessing) {
            await this.processQueue();
        }
    }

    private async processQueue() {
        if (this.queue.length === 0) {
            this.isProcessing = false;
            return;
        }

        this.isProcessing = true;
        const report = this.queue.shift()!;

        try {
            await this.sendToServer(report);
        } catch (error) {
            console.error('Failed to send error report:', error);
            // Retry later
            if (this.queue.length < 100) {
                this.queue.push(report);
            }
        }

        // Process next item
        await this.processQueue();
    }

    private async sendToServer(report: ErrorReport) {
        // Implementation depends on your error reporting service
        await api.post('/errors', {
            message: report.error.message,
            stack: report.error.stack,
            componentStack: report.errorInfo?.componentStack,
            metadata: report.metadata,
            timestamp: report.timestamp
        });
    }
}

export const errorReportingService = new ErrorReportingService();
```

## Best Practices

### 1. Error Prevention
- Use TypeScript to catch type errors at compile time
- Implement proper input validation
- Use proper type guards and assertions
- Handle edge cases explicitly

### 2. Error Recovery
- Implement retry mechanisms for transient failures
- Provide clear feedback to users
- Save user progress when possible
- Implement graceful degradation

### 3. Error Monitoring
- Log errors with sufficient context
- Track error frequencies and patterns
- Set up alerts for critical errors
- Monitor user impact

## Common Pitfalls

### 1. Silent Failures
```typescript
// Bad: Swallowing errors
try {
    await riskyOperation();
} catch {
    // Silent failure
}

// Good: Handle errors explicitly
try {
    await riskyOperation();
} catch (error) {
    if (error instanceof NetworkError) {
        showRetryPrompt();
    } else {
        reportError(error);
        showErrorMessage();
    }
}
```

### 2. Inconsistent Error Handling
```typescript
// Bad: Inconsistent error handling
async function handleSubmit() {
    try {
        await submitForm();
    } catch (error) {
        alert('Error!'); // Inconsistent UI
    }
}

// Good: Consistent error handling
async function handleSubmit() {
    try {
        await submitForm();
    } catch (error) {
        handleError(error); // Uses global error handling
    }
}
```

## Next Steps
After mastering error handling, proceed to:
1. Performance Optimization (6_performance_optimization.md) 