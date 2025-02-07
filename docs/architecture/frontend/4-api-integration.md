# 4. API Integration

## Overview
This document covers API integration patterns in our React application. These concepts build upon state management and form handling.

## API Client Setup

### 1. Axios Configuration
Setting up a base API client:

```typescript
// services/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
    baseURL: process.env.REACT_APP_API_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor
apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor
apiClient.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            // Handle unauthorized access
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default apiClient;
```

### 2. API Service Modules
Organizing API calls by domain:

```typescript
// services/api/meetings.ts
import { Meeting, MeetingFormData } from '@/types';
import apiClient from './client';

export const meetingsApi = {
    list: async () => {
        const response = await apiClient.get<Meeting[]>('/meetings');
        return response.data;
    },

    getById: async (id: number) => {
        const response = await apiClient.get<Meeting>(`/meetings/${id}`);
        return response.data;
    },

    create: async (data: MeetingFormData) => {
        const response = await apiClient.post<Meeting>('/meetings', data);
        return response.data;
    },

    update: async (id: number, data: Partial<MeetingFormData>) => {
        const response = await apiClient.put<Meeting>(`/meetings/${id}`, data);
        return response.data;
    },

    delete: async (id: number) => {
        await apiClient.delete(`/meetings/${id}`);
    }
};
```

## Data Fetching Patterns

### 1. Custom Hooks for API Calls
```typescript
// hooks/useMeetings.ts
function useMeetings() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const fetchMeetings = useCallback(async () => {
        try {
            setLoading(true);
            const data = await meetingsApi.list();
            setMeetings(data);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to fetch meetings'));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchMeetings();
    }, [fetchMeetings]);

    const refetch = useCallback(() => {
        return fetchMeetings();
    }, [fetchMeetings]);

    return { meetings, loading, error, refetch };
}
```

### 2. Pagination and Infinite Loading
```typescript
// hooks/useInfiniteMeetings.ts
interface UseMeetingsOptions {
    pageSize?: number;
    initialPage?: number;
}

function useInfiniteMeetings({ pageSize = 10, initialPage = 1 }: UseMeetingsOptions = {}) {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [page, setPage] = useState(initialPage);

    const loadMore = useCallback(async () => {
        if (loading || !hasMore) return;

        try {
            setLoading(true);
            const response = await apiClient.get<Meeting[]>('/meetings', {
                params: {
                    page,
                    pageSize
                }
            });

            const newMeetings = response.data;
            setMeetings(prev => [...prev, ...newMeetings]);
            setHasMore(newMeetings.length === pageSize);
            setPage(prev => prev + 1);
        } catch (error) {
            console.error('Failed to load meetings:', error);
        } finally {
            setLoading(false);
        }
    }, [loading, hasMore, page, pageSize]);

    return { meetings, loading, hasMore, loadMore };
}
```

## Real-Time Integration

### 1. WebSocket Setup
```typescript
// services/websocket.ts
class WebSocketService {
    private socket: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;

    connect() {
        this.socket = new WebSocket(process.env.REACT_APP_WS_URL!);

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return this.socket;
    }

    private attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting to reconnect (${this.reconnectAttempts})`);
                this.connect();
            }, 1000 * Math.pow(2, this.reconnectAttempts));
        }
    }

    send(message: any) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        }
    }
}

export const wsService = new WebSocketService();
```

### 2. Real-Time Hooks
```typescript
// hooks/useRealtimeMeeting.ts
function useRealtimeMeeting(meetingId: number) {
    const [meeting, setMeeting] = useState<Meeting | null>(null);
    const [participants, setParticipants] = useState<Participant[]>([]);
    const socket = useRef<WebSocket | null>(null);

    useEffect(() => {
        socket.current = wsService.connect();

        socket.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch (data.type) {
                case 'MEETING_UPDATED':
                    setMeeting(data.meeting);
                    break;
                case 'PARTICIPANT_JOINED':
                    setParticipants(prev => [...prev, data.participant]);
                    break;
                case 'PARTICIPANT_LEFT':
                    setParticipants(prev => 
                        prev.filter(p => p.id !== data.participantId)
                    );
                    break;
            }
        };

        // Join meeting room
        wsService.send({
            type: 'JOIN_MEETING',
            meetingId
        });

        return () => {
            wsService.send({
                type: 'LEAVE_MEETING',
                meetingId
            });
            socket.current?.close();
        };
    }, [meetingId]);

    return { meeting, participants };
}
```

## Error Handling

### 1. Global Error Handler
```typescript
// utils/errorHandler.ts
export class ApiError extends Error {
    constructor(
        public status: number,
        public message: string,
        public data?: any
    ) {
        super(message);
    }
}

export function handleApiError(error: unknown): ApiError {
    if (axios.isAxiosError(error)) {
        return new ApiError(
            error.response?.status || 500,
            error.response?.data?.message || 'An unexpected error occurred',
            error.response?.data
        );
    }
    return new ApiError(500, 'An unexpected error occurred');
}
```

### 2. Error Boundaries for API Calls
```typescript
// components/ErrorBoundary.tsx
interface Props {
    fallback: ReactNode;
    children: ReactNode;
}

class ApiErrorBoundary extends React.Component<Props, { hasError: boolean }> {
    state = { hasError: false };

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error: Error) {
        if (error instanceof ApiError) {
            // Log to error reporting service
            console.error('API Error:', error);
        }
    }

    render() {
        if (this.state.hasError) {
            return this.props.fallback;
        }
        return this.props.children;
    }
}
```

## Best Practices

### 1. Request Caching
```typescript
// hooks/useQueryCache.ts
function useQueryCache<T>(
    key: string,
    queryFn: () => Promise<T>,
    options: { ttl?: number } = {}
) {
    const cache = useRef(new Map<string, { data: T; timestamp: number }>());
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            const cached = cache.current.get(key);
            const now = Date.now();

            if (cached && (!options.ttl || now - cached.timestamp < options.ttl)) {
                setData(cached.data);
                return;
            }

            setLoading(true);
            try {
                const result = await queryFn();
                cache.current.set(key, { data: result, timestamp: now });
                setData(result);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [key, queryFn, options.ttl]);

    return { data, loading };
}
```

### 2. Request Cancellation
```typescript
function useCancellableQuery<T>(queryFn: () => Promise<T>) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const abortController = new AbortController();

        const fetchData = async () => {
            setLoading(true);
            try {
                const result = await queryFn();
                if (!abortController.signal.aborted) {
                    setData(result);
                }
            } finally {
                if (!abortController.signal.aborted) {
                    setLoading(false);
                }
            }
        };

        fetchData();

        return () => {
            abortController.abort();
        };
    }, [queryFn]);

    return { data, loading };
}
```

## Common Pitfalls

### 1. Race Conditions
```typescript
// Bad: Race condition prone
async function fetchUserData(userId: number) {
    const response = await api.get(`/users/${userId}`);
    setUser(response.data); // Might set stale data
}

// Good: Handle race conditions
function useUser(userId: number) {
    const [user, setUser] = useState(null);
    
    useEffect(() => {
        let isCurrent = true;
        
        async function fetchUser() {
            const response = await api.get(`/users/${userId}`);
            if (isCurrent) {
                setUser(response.data);
            }
        }
        
        fetchUser();
        
        return () => {
            isCurrent = false;
        };
    }, [userId]);
}
```

### 2. Error Handling
```typescript
// Bad: Generic error handling
catch (error) {
    setError('An error occurred');
}

// Good: Specific error handling
catch (error) {
    if (axios.isAxiosError(error)) {
        if (error.response?.status === 404) {
            setError('Meeting not found');
        } else if (error.response?.status === 403) {
            setError('You do not have permission to access this meeting');
        } else {
            setError('Failed to load meeting details');
        }
    }
}
```

## Next Steps
After mastering API integration, proceed to:
1. Error Handling (5_error_handling.md)
2. Performance Optimization (6_performance_optimization.md) 