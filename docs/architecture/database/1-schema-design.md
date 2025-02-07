# Database Schema Design

## Core Tables

### 1. Users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

### 2. Meetings
```sql
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by INTEGER REFERENCES users(id),
    is_recurring BOOLEAN DEFAULT false,
    recurrence_pattern VARCHAR(50),
    meeting_link VARCHAR(255),
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_time_range CHECK (end_time > start_time),
    CONSTRAINT valid_status CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled'))
);

CREATE INDEX idx_meetings_start_time ON meetings(start_time);
CREATE INDEX idx_meetings_created_by ON meetings(created_by);
```

### 3. Meeting Participants
```sql
CREATE TABLE meeting_participants (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    role VARCHAR(50) NOT NULL DEFAULT 'attendee',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(meeting_id, user_id),
    CONSTRAINT valid_participant_status CHECK (status IN ('pending', 'accepted', 'declined'))
);

CREATE INDEX idx_meeting_participants_meeting ON meeting_participants(meeting_id);
CREATE INDEX idx_meeting_participants_user ON meeting_participants(user_id);
```

## Authentication Tables

### 1. Roles
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2. User Roles
```sql
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
```

### 3. Access Tokens
```sql
CREATE TABLE access_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_revoked BOOLEAN DEFAULT false
);

CREATE INDEX idx_access_tokens_user ON access_tokens(user_id);
CREATE INDEX idx_access_tokens_token_hash ON access_tokens(token_hash);
```

## Additional Features

### 1. Meeting Resources
```sql
CREATE TABLE meeting_resources (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url VARCHAR(255),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meeting_resources_meeting ON meeting_resources(meeting_id);
```

### 2. Meeting Notes
```sql
CREATE TABLE meeting_notes (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    content TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_meeting_notes_meeting ON meeting_notes(meeting_id);
```

### 3. Notifications
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

## Schema Design Principles

### 1. Normalization
- Tables are in Third Normal Form (3NF)
- Avoid data redundancy
- Maintain data integrity
- Use appropriate relationships
- Balance normalization with performance

### 2. Relationships
```sql
-- One-to-Many relationship (User -> Meetings)
ALTER TABLE meetings
ADD CONSTRAINT fk_meeting_creator
FOREIGN KEY (created_by) REFERENCES users(id);

-- Many-to-Many relationship (Meetings <-> Users)
CREATE TABLE meeting_participants (
    meeting_id INTEGER,
    user_id INTEGER,
    PRIMARY KEY (meeting_id, user_id),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- One-to-Many with additional attributes
CREATE TABLE meeting_notes (
    id SERIAL PRIMARY KEY,
    meeting_id INTEGER,
    content TEXT,
    created_by INTEGER,
    FOREIGN KEY (meeting_id) REFERENCES meetings(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

### 3. Indexing Strategy
```sql
-- Primary key indexes (automatically created)
-- meetings(id)
-- users(id)

-- Foreign key indexes
CREATE INDEX idx_meetings_created_by ON meetings(created_by);
CREATE INDEX idx_meeting_participants_user ON meeting_participants(user_id);
CREATE INDEX idx_meeting_participants_meeting ON meeting_participants(meeting_id);

-- Performance indexes
CREATE INDEX idx_meetings_time_range ON meetings(start_time, end_time);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_meetings_status ON meetings(status);

-- Composite indexes for common queries
CREATE INDEX idx_meeting_participants_status 
ON meeting_participants(meeting_id, user_id, status);
```

## Data Types and Constraints

### 1. Common Data Types
```sql
-- String types
title VARCHAR(100)       -- Fixed maximum length
description TEXT         -- Unlimited length text
status VARCHAR(20)       -- Enumerated values

-- Numeric types
id SERIAL               -- Auto-incrementing integer
count INTEGER           -- Whole numbers
amount DECIMAL(10,2)    -- Precise decimal numbers

-- Date/Time types
created_at TIMESTAMP    -- Date and time
start_date DATE        -- Date only
duration INTERVAL      -- Time duration

-- Boolean type
is_active BOOLEAN      -- True/False values

-- JSON type
metadata JSONB         -- Binary JSON data
```

### 2. Constraints
```sql
-- Primary Key constraints
PRIMARY KEY (id)
PRIMARY KEY (meeting_id, user_id)  -- Composite key

-- Foreign Key constraints
FOREIGN KEY (user_id) REFERENCES users(id)
FOREIGN KEY (meeting_id) REFERENCES meetings(id)

-- Unique constraints
UNIQUE (email)
UNIQUE (name, type)  -- Composite unique

-- Check constraints
CHECK (end_time > start_time)
CHECK (status IN ('scheduled', 'completed', 'cancelled'))

-- Not Null constraints
name VARCHAR(100) NOT NULL
email VARCHAR(120) NOT NULL
```

## Best Practices

### 1. Schema Design
- Use appropriate data types
- Implement proper constraints
- Design for scalability
- Consider query patterns
- Maintain documentation

### 2. Performance
- Create necessary indexes
- Avoid over-indexing
- Use appropriate constraints
- Monitor query performance
- Regular maintenance

### 3. Security
- Implement proper access control
- Use parameterized queries
- Encrypt sensitive data
- Regular security audits
- Backup strategies

## Common Pitfalls

### 1. Poor Schema Design
```sql
-- Bad: Storing comma-separated values
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    participant_ids TEXT  -- Storing "1,2,3,4"
);

-- Good: Using a proper junction table
CREATE TABLE meeting_participants (
    meeting_id INTEGER REFERENCES meetings(id),
    user_id INTEGER REFERENCES users(id),
    PRIMARY KEY (meeting_id, user_id)
);
```

### 2. Missing Indexes
```sql
-- Bad: No index on frequently queried column
SELECT * FROM meetings WHERE status = 'scheduled';

-- Good: Add index for better performance
CREATE INDEX idx_meetings_status ON meetings(status);
```

### 3. Improper Constraints
```sql
-- Bad: No data validation
CREATE TABLE meetings (
    start_time TIMESTAMP,
    end_time TIMESTAMP
);

-- Good: Add proper constraints
CREATE TABLE meetings (
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);
```

## Next Steps
1. Review [Data Migration](2-data-migration.md)
2. Explore [Query Optimization](3-query-optimization.md)
3. Learn about [Database Maintenance](4-maintenance.md) 