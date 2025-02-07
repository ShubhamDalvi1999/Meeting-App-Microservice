# 6. Performance Optimization

## Overview
This document covers performance optimization techniques in our React application. These concepts help ensure a smooth and responsive user experience.

## Component Optimization

### 1. Memoization
Using React.memo and useMemo:

```typescript
// components/meetings/MeetingCard.tsx
interface MeetingCardProps {
    meeting: Meeting;
    onJoin: (id: number) => void;
}

const MeetingCard = React.memo(function MeetingCard({ 
    meeting, 
    onJoin 
}: MeetingCardProps) {
    const formattedDate = useMemo(() => 
        formatDate(meeting.startTime),
        [meeting.startTime]
    );

    const participantCount = useMemo(() => 
        meeting.participants.length,
        [meeting.participants]
    );

    return (
        <div className="meeting-card">
            <h3>{meeting.title}</h3>
            <p>{meeting.description}</p>
            <time>{formattedDate}</time>
            <div>Participants: {participantCount}</div>
            <button onClick={() => onJoin(meeting.id)}>Join</button>
        </div>
    );
}, (prevProps, nextProps) => {
    // Custom comparison function
    return (
        prevProps.meeting.id === nextProps.meeting.id &&
        prevProps.meeting.updatedAt === nextProps.meeting.updatedAt
    );
});
```

### 2. Callback Optimization
Using useCallback for event handlers:

```typescript
// components/meetings/MeetingsList.tsx
function MeetingsList() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);

    const handleJoin = useCallback((id: number) => {
        joinMeeting(id);
    }, []);

    const handleDelete = useCallback(async (id: number) => {
        try {
            await deleteMeeting(id);
            setMeetings(prev => prev.filter(m => m.id !== id));
        } catch (error) {
            handleError(error);
        }
    }, []);

    return (
        <div className="meetings-list">
            {meetings.map(meeting => (
                <MeetingCard
                    key={meeting.id}
                    meeting={meeting}
                    onJoin={handleJoin}
                    onDelete={handleDelete}
                />
            ))}
        </div>
    );
}
```

## Rendering Optimization

### 1. Virtual Lists
Implementing virtualized lists for large datasets:

```typescript
// components/common/VirtualList.tsx
interface VirtualListProps<T> {
    items: T[];
    height: number;
    itemHeight: number;
    renderItem: (item: T, index: number) => ReactNode;
}

function VirtualList<T>({
    items,
    height,
    itemHeight,
    renderItem
}: VirtualListProps<T>) {
    const [scrollTop, setScrollTop] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    const visibleItems = useMemo(() => {
        const startIndex = Math.floor(scrollTop / itemHeight);
        const endIndex = Math.min(
            startIndex + Math.ceil(height / itemHeight),
            items.length
        );

        return items.slice(startIndex, endIndex).map((item, index) => ({
            item,
            index: startIndex + index,
            offsetY: (startIndex + index) * itemHeight
        }));
    }, [items, scrollTop, height, itemHeight]);

    const handleScroll = useCallback((e: UIEvent) => {
        setScrollTop(e.currentTarget.scrollTop);
    }, []);

    return (
        <div
            ref={containerRef}
            style={{ height, overflow: 'auto' }}
            onScroll={handleScroll}
        >
            <div style={{ height: items.length * itemHeight }}>
                {visibleItems.map(({ item, index, offsetY }) => (
                    <div
                        key={index}
                        style={{
                            position: 'absolute',
                            top: offsetY,
                            height: itemHeight
                        }}
                    >
                        {renderItem(item, index)}
                    </div>
                ))}
            </div>
        </div>
    );
}

// Usage
function MeetingsList() {
    return (
        <VirtualList
            items={meetings}
            height={600}
            itemHeight={100}
            renderItem={(meeting) => (
                <MeetingCard meeting={meeting} />
            )}
        />
    );
}
```

### 2. Lazy Loading
Implementing lazy loading for components and routes:

```typescript
// routes/index.tsx
const MeetingsDashboard = lazy(() => import('./pages/MeetingsDashboard'));
const MeetingDetails = lazy(() => import('./pages/MeetingDetails'));
const CreateMeeting = lazy(() => import('./pages/CreateMeeting'));

function AppRoutes() {
    return (
        <Suspense fallback={<LoadingSpinner />}>
            <Routes>
                <Route path="/meetings" element={<MeetingsDashboard />} />
                <Route path="/meetings/:id" element={<MeetingDetails />} />
                <Route path="/meetings/create" element={<CreateMeeting />} />
            </Routes>
        </Suspense>
    );
}
```

## State Management Optimization

### 1. Context Optimization
Splitting context to prevent unnecessary re-renders:

```typescript
// contexts/meetings/MeetingsContext.tsx
interface MeetingsState {
    meetings: Meeting[];
    loading: boolean;
}

interface MeetingsActions {
    addMeeting: (meeting: Meeting) => void;
    removeMeeting: (id: number) => void;
    updateMeeting: (id: number, updates: Partial<Meeting>) => void;
}

const MeetingsStateContext = createContext<MeetingsState | null>(null);
const MeetingsActionsContext = createContext<MeetingsActions | null>(null);

function MeetingsProvider({ children }: { children: ReactNode }) {
    const [state, dispatch] = useReducer(meetingsReducer, initialState);

    const actions = useMemo(() => ({
        addMeeting: (meeting) => 
            dispatch({ type: 'ADD_MEETING', payload: meeting }),
        removeMeeting: (id) => 
            dispatch({ type: 'REMOVE_MEETING', payload: id }),
        updateMeeting: (id, updates) => 
            dispatch({ type: 'UPDATE_MEETING', payload: { id, updates } })
    }), []);

    return (
        <MeetingsStateContext.Provider value={state}>
            <MeetingsActionsContext.Provider value={actions}>
                {children}
            </MeetingsActionsContext.Provider>
        </MeetingsStateContext.Provider>
    );
}
```

### 2. State Updates Batching
Optimizing state updates:

```typescript
// hooks/useMeetingUpdates.ts
function useMeetingUpdates() {
    const [updates, setUpdates] = useState<Map<number, Partial<Meeting>>>(
        new Map()
    );
    const timeoutRef = useRef<NodeJS.Timeout>();

    const scheduleUpdate = useCallback((
        meetingId: number, 
        update: Partial<Meeting>
    ) => {
        setUpdates(prev => {
            const next = new Map(prev);
            const existing = next.get(meetingId) || {};
            next.set(meetingId, { ...existing, ...update });
            return next;
        });

        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }

        timeoutRef.current = setTimeout(() => {
            flushUpdates();
        }, 1000);
    }, []);

    const flushUpdates = useCallback(async () => {
        const currentUpdates = new Map(updates);
        setUpdates(new Map());

        for (const [id, update] of currentUpdates) {
            try {
                await api.meetings.update(id, update);
            } catch (error) {
                handleError(error);
                // Restore failed updates
                setUpdates(prev => {
                    const next = new Map(prev);
                    next.set(id, update);
                    return next;
                });
            }
        }
    }, [updates]);

    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    return { scheduleUpdate, flushUpdates };
}
```

## Network Optimization

### 1. Request Caching
Implementing a caching layer:

```typescript
// utils/cache.ts
class Cache<T> {
    private cache = new Map<string, {
        data: T;
        timestamp: number;
        ttl: number;
    }>();

    set(key: string, data: T, ttl: number) {
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            ttl
        });
    }

    get(key: string): T | null {
        const entry = this.cache.get(key);
        if (!entry) return null;

        if (Date.now() - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            return null;
        }

        return entry.data;
    }

    clear() {
        this.cache.clear();
    }
}

// hooks/useQueryCache.ts
function useQueryCache<T>(
    key: string,
    queryFn: () => Promise<T>,
    options: { ttl?: number } = {}
) {
    const cache = useRef(new Cache<T>());
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            const cached = cache.current.get(key);
            if (cached) {
                setData(cached);
                return;
            }

            setLoading(true);
            try {
                const result = await queryFn();
                cache.current.set(key, result, options.ttl || 5 * 60 * 1000);
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

### 2. Request Deduplication
Preventing duplicate requests:

```typescript
// utils/requestDeduplication.ts
class RequestDeduplicator {
    private pending = new Map<string, Promise<any>>();

    async deduplicate<T>(
        key: string,
        request: () => Promise<T>
    ): Promise<T> {
        if (this.pending.has(key)) {
            return this.pending.get(key);
        }

        const promise = request().finally(() => {
            this.pending.delete(key);
        });

        this.pending.set(key, promise);
        return promise;
    }
}

const deduplicator = new RequestDeduplicator();

// Usage
async function fetchMeeting(id: number) {
    return deduplicator.deduplicate(
        `meeting-${id}`,
        () => api.meetings.getById(id)
    );
}
```

## Best Practices

### 1. Code Splitting
- Use dynamic imports for routes
- Split vendor code
- Implement progressive loading
- Use prefetching for critical paths

### 2. Asset Optimization
- Optimize images and media
- Use appropriate image formats
- Implement lazy loading for images
- Compress static assets

### 3. Monitoring
- Track performance metrics
- Monitor bundle size
- Implement error tracking
- Use performance profiling tools

## Common Pitfalls

### 1. Unnecessary Re-renders
```typescript
// Bad: Inline object creation
function BadComponent() {
    return (
        <MeetingCard
            meeting={meeting}
            style={{ margin: '10px' }} // New object every render
            onJoin={() => handleJoin(meeting.id)} // New function every render
        />
    );
}

// Good: Memoized values
function GoodComponent() {
    const style = useMemo(() => ({ margin: '10px' }), []);
    const handleJoin = useCallback(
        (id: number) => handleJoin(id),
        []
    );

    return (
        <MeetingCard
            meeting={meeting}
            style={style}
            onJoin={handleJoin}
        />
    );
}
```

### 2. Memory Leaks
```typescript
// Bad: Memory leak in subscription
function BadComponent() {
    useEffect(() => {
        const subscription = eventEmitter.subscribe(handleEvent);
        // Missing cleanup
    }, []);
}

// Good: Proper cleanup
function GoodComponent() {
    useEffect(() => {
        const subscription = eventEmitter.subscribe(handleEvent);
        return () => {
            subscription.unsubscribe();
        };
    }, []);
}
```

## Next Steps
After mastering frontend performance optimization, proceed to the backend documentation:
1. Basic Concepts (1_basic_concepts.md)
2. Authentication & Authorization (2_auth.md)
3. Database Operations (3_database.md)
4. Error Handling (4_error_handling.md)
5. Testing (5_testing.md) 