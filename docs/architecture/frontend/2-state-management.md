# 2. State Management

## Overview
This document covers state management patterns in our React application. Understanding these concepts is crucial after mastering basic component structure.

## Local State Management

### 1. useState Hook
The foundation of React state management:

```typescript
function MeetingForm() {
    // Simple state
    const [title, setTitle] = useState('');
    
    // Object state
    const [formData, setFormData] = useState<MeetingFormData>({
        title: '',
        description: '',
        startTime: new Date(),
        endTime: new Date()
    });
    
    // Updating object state
    const handleChange = (field: keyof MeetingFormData) => (
        value: MeetingFormData[typeof field]
    ) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
    };
}
```

### 2. useReducer Hook
For complex state logic:

```typescript
type MeetingState = {
    meetings: Meeting[];
    loading: boolean;
    error: string | null;
    selectedMeeting: Meeting | null;
};

type MeetingAction = 
    | { type: 'FETCH_START' }
    | { type: 'FETCH_SUCCESS'; payload: Meeting[] }
    | { type: 'FETCH_ERROR'; payload: string }
    | { type: 'SELECT_MEETING'; payload: Meeting }
    | { type: 'CLEAR_SELECTION' };

function meetingReducer(state: MeetingState, action: MeetingAction): MeetingState {
    switch (action.type) {
        case 'FETCH_START':
            return {
                ...state,
                loading: true,
                error: null
            };
        case 'FETCH_SUCCESS':
            return {
                ...state,
                meetings: action.payload,
                loading: false
            };
        case 'FETCH_ERROR':
            return {
                ...state,
                error: action.payload,
                loading: false
            };
        case 'SELECT_MEETING':
            return {
                ...state,
                selectedMeeting: action.payload
            };
        case 'CLEAR_SELECTION':
            return {
                ...state,
                selectedMeeting: null
            };
        default:
            return state;
    }
}

function MeetingList() {
    const [state, dispatch] = useReducer(meetingReducer, {
        meetings: [],
        loading: false,
        error: null,
        selectedMeeting: null
    });

    useEffect(() => {
        const fetchMeetings = async () => {
            dispatch({ type: 'FETCH_START' });
            try {
                const data = await api.meetings.list();
                dispatch({ type: 'FETCH_SUCCESS', payload: data });
            } catch (error) {
                dispatch({ 
                    type: 'FETCH_ERROR', 
                    payload: error.message 
                });
            }
        };

        fetchMeetings();
    }, []);
}
```

## Global State Management

### 1. React Context
For sharing state across components:

```typescript
// contexts/MeetingContext.tsx
interface MeetingContextType {
    meetings: Meeting[];
    selectedMeeting: Meeting | null;
    selectMeeting: (meeting: Meeting) => void;
    clearSelection: () => void;
}

const MeetingContext = createContext<MeetingContextType | null>(null);

export function MeetingProvider({ children }: { children: ReactNode }) {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);

    const selectMeeting = useCallback((meeting: Meeting) => {
        setSelectedMeeting(meeting);
    }, []);

    const clearSelection = useCallback(() => {
        setSelectedMeeting(null);
    }, []);

    return (
        <MeetingContext.Provider 
            value={{ 
                meetings, 
                selectedMeeting, 
                selectMeeting, 
                clearSelection 
            }}
        >
            {children}
        </MeetingContext.Provider>
    );
}

// Custom hook for using the context
export function useMeetingContext() {
    const context = useContext(MeetingContext);
    if (!context) {
        throw new Error('useMeetingContext must be used within MeetingProvider');
    }
    return context;
}
```

### 2. Custom Hooks
For reusable state logic:

```typescript
function useMeetingActions() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const createMeeting = async (data: MeetingFormData) => {
        setLoading(true);
        setError(null);
        try {
            const result = await api.meetings.create(data);
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const updateMeeting = async (id: number, data: Partial<MeetingFormData>) => {
        setLoading(true);
        setError(null);
        try {
            const result = await api.meetings.update(id, data);
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return {
        loading,
        error,
        createMeeting,
        updateMeeting
    };
}
```

## State Management Patterns

### 1. Lifting State Up
```typescript
function MeetingDashboard() {
    // Lift state to common ancestor
    const [selectedMeetingId, setSelectedMeetingId] = useState<number | null>(null);

    return (
        <div className="dashboard">
            <MeetingList
                onSelectMeeting={setSelectedMeetingId}
                selectedMeetingId={selectedMeetingId}
            />
            <MeetingDetails
                meetingId={selectedMeetingId}
                onClose={() => setSelectedMeetingId(null)}
            />
        </div>
    );
}
```

### 2. State Composition
```typescript
function useMeetingState() {
    const meetings = useMeetings(); // Fetches meetings
    const participants = useParticipants(); // Fetches participants
    const permissions = usePermissions(); // Fetches user permissions

    // Combine states
    const enrichedMeetings = useMemo(() => 
        meetings.data.map(meeting => ({
            ...meeting,
            participants: participants.data[meeting.id] || [],
            canEdit: permissions.canEditMeeting(meeting.id)
        })),
        [meetings.data, participants.data, permissions]
    );

    return {
        meetings: enrichedMeetings,
        loading: meetings.loading || participants.loading || permissions.loading,
        error: meetings.error || participants.error || permissions.error
    };
}
```

## Best Practices

### 1. State Location
- Keep state as close as possible to where it's used
- Lift state up only when necessary
- Use context for truly global state
- Split context by domain/feature

### 2. State Updates
- Use functional updates for state that depends on previous state
- Batch related state updates
- Memoize callbacks that update state
- Use reducers for complex state logic

### 3. Performance
- Avoid unnecessary re-renders
- Use appropriate memoization
- Split context to prevent unnecessary updates
- Implement optimistic updates when appropriate

## Common Pitfalls

### 1. Unnecessary Global State
```typescript
// Bad: Global state for local concern
const GlobalContext = createContext<{ activeTab: string }>(null);

// Good: Keep local state local
function Tabs() {
    const [activeTab, setActiveTab] = useState('home');
    return <TabList activeTab={activeTab} onChange={setActiveTab} />;
}
```

### 2. State Update Race Conditions
```typescript
// Bad: Race condition prone
function Counter() {
    const [count, setCount] = useState(0);
    
    const increment = () => {
        setCount(count + 1); // Uses stale count
    };

    // Good: Use functional update
    const increment = () => {
        setCount(prev => prev + 1);
    };
}
```

## Next Steps
After mastering state management, proceed to:
1. Forms and Validation (3_forms_and_validation.md)
2. API Integration (4_api_integration.md)
3. Error Handling (5_error_handling.md)
4. Performance Optimization (6_performance_optimization.md) 