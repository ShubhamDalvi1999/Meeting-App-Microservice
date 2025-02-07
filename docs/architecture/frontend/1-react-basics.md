# Frontend Application Documentation

## Overview
The frontend is a modern, responsive web application built with Next.js and React, providing a seamless user experience for video conferencing and collaboration.

## Component Types

### 1. Functional Components
Modern React applications primarily use functional components with hooks:

```typescript
// Basic functional component
function WelcomeBanner({ username }: { username: string }) {
    return (
        <div className="welcome-banner">
            <h1>Welcome, {username}!</h1>
        </div>
    );
}

// Component with props interface
interface UserAvatarProps {
    imageUrl: string;
    size?: 'small' | 'medium' | 'large';
    onClick?: () => void;
}

function UserAvatar({ imageUrl, size = 'medium', onClick }: UserAvatarProps) {
    return (
        <img 
            src={imageUrl}
            className={`avatar avatar-${size}`}
            onClick={onClick}
            alt="User avatar"
        />
    );
}
```

### 2. Component Organization

#### Page Components
High-level components that represent entire pages:

```typescript
// pages/Login.tsx
export default function Login() {
    return (
        <div className="login-page">
            <LoginForm />
            <ForgotPasswordLink />
            <SignUpPrompt />
        </div>
    );
}
```

#### Feature Components
Reusable components that implement specific features:

```typescript
// components/meetings/MeetingCard.tsx
interface MeetingCardProps {
    meeting: Meeting;
    onJoin?: (meetingId: number) => void;
    onEdit?: (meetingId: number) => void;
    variant?: 'compact' | 'full';
}

export function MeetingCard({ 
    meeting, 
    onJoin, 
    onEdit,
    variant = 'full' 
}: MeetingCardProps) {
    const formattedDate = useMemo(() => 
        formatDate(meeting.startTime), 
        [meeting.startTime]
    );

    return (
        <div className={`meeting-card meeting-card-${variant}`}>
            <div className="meeting-card-header">
                <h3>{meeting.title}</h3>
                {variant === 'full' && (
                    <div className="meeting-card-actions">
                        {onEdit && (
                            <button onClick={() => onEdit(meeting.id)}>
                                Edit
                            </button>
                        )}
                        {onJoin && (
                            <button onClick={() => onJoin(meeting.id)}>
                                Join
                            </button>
                        )}
                    </div>
                )}
            </div>
            <div className="meeting-card-content">
                <p>{meeting.description}</p>
                <time>{formattedDate}</time>
            </div>
        </div>
    );
}
```

#### Layout Components
Components that define the structure of the application:

```typescript
// components/layout/MainLayout.tsx
interface MainLayoutProps {
    children: ReactNode;
    showSidebar?: boolean;
}

export function MainLayout({ children, showSidebar = true }: MainLayoutProps) {
    return (
        <div className="main-layout">
            <Header />
            <div className="content-wrapper">
                {showSidebar && <Sidebar />}
                <main className="main-content">
                    {children}
                </main>
            </div>
            <Footer />
        </div>
    );
}
```

## Component Composition

### 1. Props and Children
```typescript
// components/common/Card.tsx
interface CardProps {
    title: string;
    children: ReactNode;
    className?: string;
    headerActions?: ReactNode;
}

function Card({ title, children, className, headerActions }: CardProps) {
    return (
        <div className={`card ${className || ''}`}>
            <div className="card-header">
                <h2>{title}</h2>
                {headerActions}
            </div>
            <div className="card-content">
                {children}
            </div>
        </div>
    );
}

// Usage
function MeetingDetails({ meeting }: { meeting: Meeting }) {
    return (
        <Card 
            title={meeting.title}
            headerActions={
                <button onClick={() => handleEdit(meeting.id)}>
                    Edit
                </button>
            }
        >
            <p>{meeting.description}</p>
            <MeetingParticipants participants={meeting.participants} />
        </Card>
    );
}
```

### 2. Component Patterns

#### Compound Components
```typescript
// components/common/Tabs.tsx
interface TabsContext {
    activeTab: string;
    setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContext | null>(null);

function Tabs({ children, defaultTab }: TabsProps) {
    const [activeTab, setActiveTab] = useState(defaultTab);

    return (
        <TabsContext.Provider value={{ activeTab, setActiveTab }}>
            <div className="tabs">{children}</div>
        </TabsContext.Provider>
    );
}

function TabList({ children }: { children: ReactNode }) {
    return <div className="tab-list">{children}</div>;
}

function Tab({ id, children }: { id: string; children: ReactNode }) {
    const context = useContext(TabsContext);
    if (!context) throw new Error('Tab must be used within Tabs');

    return (
        <button
            className={`tab ${context.activeTab === id ? 'active' : ''}`}
            onClick={() => context.setActiveTab(id)}
        >
            {children}
        </button>
    );
}

function TabPanel({ id, children }: { id: string; children: ReactNode }) {
    const context = useContext(TabsContext);
    if (!context) throw new Error('TabPanel must be used within Tabs');

    if (context.activeTab !== id) return null;
    return <div className="tab-panel">{children}</div>;
}

// Usage
function MeetingTabs() {
    return (
        <Tabs defaultTab="upcoming">
            <TabList>
                <Tab id="upcoming">Upcoming Meetings</Tab>
                <Tab id="past">Past Meetings</Tab>
            </TabList>
            <TabPanel id="upcoming">
                <UpcomingMeetingsList />
            </TabPanel>
            <TabPanel id="past">
                <PastMeetingsList />
            </TabPanel>
        </Tabs>
    );
}
```

## Purpose
- Provide an intuitive interface for video meetings
- Enable real-time collaboration features
- Ensure responsive design across devices
- Maintain high performance and accessibility

## Key Components

### 1. Authentication Module
- **Login Component**
  - User authentication form
  - JWT token management
  - Session persistence
  - Error handling

- **Registration Component**
  - User registration form
  - Input validation
  - Success/error feedback

### 2. Meeting Module

#### Video Conference Component
- WebRTC integration for video/audio streaming
- Camera and microphone controls
- Screen sharing functionality
- Grid layout for participants
- Bandwidth and quality management

#### Chat Component
- Real-time message exchange
- File sharing support
- Emoji support
- Message persistence
- Unread message indicators

#### Whiteboard Component
- Real-time drawing capabilities
- Tool selection (pen, shapes, text)
- Color and stroke management
- Canvas synchronization
- Undo/redo functionality

### 3. Meeting Management
- Meeting creation interface
- Participant invitation system
- Meeting scheduling
- Calendar integration
- Meeting settings management

## Technical Architecture

### State Management
1. **Redux Store**
   - User authentication state
   - Meeting configuration
   - Application settings
   - Cache management

2. **Local State**
   - Component-specific UI states
   - Form handling
   - Temporary data storage

### Network Layer
1. **API Integration**
   - RESTful API calls to Flask backend
   - Error handling and retries
   - Request/response interceptors
   - Cache management

2. **WebSocket Integration**
   - Real-time communication with Node.js backend
   - Connection management
   - Event handling
   - Reconnection strategies

### Media Handling
1. **WebRTC Implementation**
   - Peer connection management
   - Media stream handling
   - ICE candidate negotiation
   - Fallback mechanisms

2. **Media Processing**
   - Video/audio quality optimization
   - Background blur/replacement
   - Noise suppression
   - Echo cancellation

## Best Practices

### 1. Component Organization
- Keep components focused and single-responsibility
- Use consistent naming conventions
- Implement proper type definitions
- Follow React best practices

### 2. Performance
- Implement proper memoization
- Use React.memo for expensive renders
- Optimize re-renders
- Implement code splitting

### 3. Testing
- Write unit tests for components
- Implement integration tests
- Use proper mocking
- Test error scenarios

## Common Pitfalls

### 1. State Management
```typescript
// Bad: Prop drilling
function GrandParent() {
    const [value, setValue] = useState('');
    return <Parent value={value} setValue={setValue} />;
}

// Good: Context API
const ValueContext = createContext<ValueContextType | null>(null);

function GrandParent() {
    const [value, setValue] = useState('');
    return (
        <ValueContext.Provider value={{ value, setValue }}>
            <Parent />
        </ValueContext.Provider>
    );
}
```

### 2. Performance Issues
```typescript
// Bad: Unnecessary re-renders
function Component({ data }) {
    const processedData = heavyProcessing(data);
    return <div>{processedData}</div>;
}

// Good: Memoization
function Component({ data }) {
    const processedData = useMemo(
        () => heavyProcessing(data),
        [data]
    );
    return <div>{processedData}</div>;
}
```

## Next Steps
1. Review [State Management](2-state-management.md)
2. Explore [Forms and Validation](3-forms-validation.md)
3. Learn about [API Integration](4-api-integration.md) 