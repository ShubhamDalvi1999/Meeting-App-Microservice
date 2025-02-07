# React Components and Frontend Architecture

## Overview
This document explains the intermediate concepts of React components and frontend architecture in our meeting management system, using real examples from our application.

## Component Structure

### 1. Page Components
High-level components that represent entire pages:

```typescript
// pages/dashboard.tsx
export default function Dashboard() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchMeetings();
    }, []);

    return (
        <Layout>
            <MeetingList meetings={meetings} />
            <CreateMeetingButton />
        </Layout>
    );
}
```

### 2. Feature Components
Reusable components that implement specific features:

```typescript
// components/MeetingList.tsx
interface MeetingListProps {
    meetings: Meeting[];
    onJoin?: (meetingId: number) => void;
}

export function MeetingList({ meetings, onJoin }: MeetingListProps) {
    return (
        <div className="meeting-list">
            {meetings.map(meeting => (
                <MeetingCard 
                    key={meeting.id} 
                    meeting={meeting}
                    onJoin={onJoin}
                />
            ))}
        </div>
    );
}
```

## State Management

### 1. Local State
Using React's useState for component-level state:

```typescript
function CreateMeetingForm() {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [startTime, setStartTime] = useState<Date | null>(null);
    
    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        // Form submission logic
    };
}
```

### 2. Context API
Managing global state with React Context:

```typescript
// contexts/AuthContext.tsx
export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);

    const login = async (email: string, password: string) => {
        // Login logic
    };

    return (
        <AuthContext.Provider value={{ user, token, login }}>
            {children}
        </AuthContext.Provider>
    );
}
```

## API Integration

### 1. API Calls
Using fetch or axios for API requests:

```typescript
async function fetchMeetings() {
    try {
        const response = await fetch('/api/meetings/list', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch meetings');
        }
        
        const data = await response.json();
        setMeetings(data);
    } catch (error) {
        setError('Failed to load meetings');
    }
}
```

### 2. Custom Hooks
Encapsulating API logic in custom hooks:

```typescript
function useMeetings() {
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchMeetings()
            .then(data => setMeetings(data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    return { meetings, loading, error };
}
```

## Form Handling

### 1. Form Components
```typescript
function MeetingForm({ onSubmit }: MeetingFormProps) {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        startTime: '',
        endTime: ''
    });

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    return (
        <form onSubmit={handleSubmit}>
            <Input
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
            />
            {/* Other form fields */}
        </form>
    );
}
```

### 2. Form Validation
```typescript
function validateMeetingForm(data: MeetingFormData) {
    const errors: Partial<MeetingFormData> = {};
    
    if (!data.title.trim()) {
        errors.title = 'Title is required';
    }
    
    if (new Date(data.startTime) < new Date()) {
        errors.startTime = 'Meeting cannot start in the past';
    }
    
    return errors;
}
```

## Error Handling

### 1. Error Boundaries
```typescript
class ErrorBoundary extends React.Component<Props, State> {
    state = { hasError: false, error: null };

    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }

    render() {
        if (this.state.hasError) {
            return <ErrorDisplay error={this.state.error} />;
        }
        return this.props.children;
    }
}
```

### 2. Error States
```typescript
function MeetingView() {
    const [error, setError] = useState<string | null>(null);

    if (error) {
        return (
            <ErrorAlert 
                message={error}
                onDismiss={() => setError(null)}
            />
        );
    }

    return <MeetingContent />;
}
```

## Performance Optimization

### 1. Memoization
```typescript
const MemoizedMeetingCard = React.memo(function MeetingCard({ 
    meeting,
    onJoin
}: MeetingCardProps) {
    return (
        <div className="meeting-card">
            <h3>{meeting.title}</h3>
            <p>{meeting.description}</p>
            <button onClick={() => onJoin(meeting.id)}>
                Join Meeting
            </button>
        </div>
    );
});
```

### 2. Lazy Loading
```typescript
const CreateMeetingModal = React.lazy(() => 
    import('./components/CreateMeetingModal')
);

function Dashboard() {
    return (
        <Suspense fallback={<LoadingSpinner />}>
            <CreateMeetingModal />
        </Suspense>
    );
}
```

## Testing

### 1. Component Testing
```typescript
describe('MeetingList', () => {
    it('renders meetings correctly', () => {
        const meetings = [
            { id: 1, title: 'Test Meeting' }
        ];
        
        render(<MeetingList meetings={meetings} />);
        expect(screen.getByText('Test Meeting')).toBeInTheDocument();
    });
});
```

### 2. Integration Testing
```typescript
test('creating a new meeting', async () => {
    render(<CreateMeetingForm />);
    
    fireEvent.change(
        screen.getByLabelText('Title'),
        { target: { value: 'New Meeting' } }
    );
    
    fireEvent.click(screen.getByText('Create'));
    
    await waitFor(() => {
        expect(screen.getByText('Meeting created')).toBeInTheDocument();
    });
});
``` 