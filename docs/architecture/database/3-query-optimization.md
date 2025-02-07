# 3. Query Optimization

## Overview
This document covers query optimization strategies in our meeting management system. Understanding these concepts is crucial for maintaining application performance and efficient database operations.

## Query Analysis

### 1. EXPLAIN ANALYZE
```sql
-- Example: Analyzing query performance
EXPLAIN ANALYZE
SELECT m.*, u.name as creator_name
FROM meetings m
JOIN users u ON m.created_by = u.id
WHERE m.start_time > NOW()
ORDER BY m.start_time;

-- Output analysis
Nested Loop  (cost=4.17..32.27 rows=10 width=325)
  ->  Index Scan using meetings_start_time_idx on meetings m  (cost=0.15..8.17 rows=10 width=325)
        Filter: (start_time > now())
  ->  Index Scan using users_pkey on users u  (cost=0.14..2.65 rows=1 width=32)
        Index Cond: (id = m.created_by)
```

### 2. Query Statistics
```sql
-- Example: Gathering query statistics
SELECT relname as table_name,
       n_live_tup as row_count,
       n_dead_tup as dead_rows
FROM pg_stat_user_tables
WHERE schemaname = 'public';

-- Example: Index usage statistics
SELECT schemaname,
       relname,
       indexrelname,
       idx_scan as number_of_scans,
       idx_tup_read as tuples_read,
       idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public';
```

## Query Optimization Techniques

### 1. Index Optimization
```sql
-- Example: Composite index for common query pattern
CREATE INDEX idx_meetings_creator_time 
ON meetings (created_by, start_time);

-- Example: Partial index for specific conditions
CREATE INDEX idx_active_meetings 
ON meetings (start_time) 
WHERE status = 'scheduled';

-- Example: Expression index
CREATE INDEX idx_lower_email 
ON users (LOWER(email));

-- Query using expression index
SELECT * FROM users 
WHERE LOWER(email) = LOWER('User@Example.com');
```

### 2. JOIN Optimization
```sql
-- Example: Optimizing JOIN queries
-- Bad: Cartesian product
SELECT m.*, u.*
FROM meetings m, users u
WHERE m.created_by = u.id;

-- Good: Explicit JOIN with proper conditions
SELECT m.*, u.*
FROM meetings m
JOIN users u ON m.created_by = u.id;

-- Example: Using subqueries effectively
-- Bad: Correlated subquery
SELECT m.*,
       (SELECT COUNT(*) 
        FROM meeting_participants mp 
        WHERE mp.meeting_id = m.id) as participant_count
FROM meetings m;

-- Good: Using JOIN and GROUP BY
SELECT m.*, COUNT(mp.user_id) as participant_count
FROM meetings m
LEFT JOIN meeting_participants mp ON m.id = mp.meeting_id
GROUP BY m.id;
```

### 3. Pagination Optimization
```sql
-- Bad: Offset-based pagination
SELECT *
FROM meetings
ORDER BY start_time
LIMIT 10 OFFSET 1000000;

-- Good: Keyset-based pagination
SELECT *
FROM meetings
WHERE start_time > :last_seen_time
ORDER BY start_time
LIMIT 10;

-- Example: Optimized pagination with cursor
WITH ranked_meetings AS (
    SELECT m.*,
           ROW_NUMBER() OVER (
               ORDER BY start_time, id
           ) as row_num
    FROM meetings m
    WHERE created_by = :user_id
)
SELECT *
FROM ranked_meetings
WHERE row_num BETWEEN :start AND :end;
```

## Query Patterns

### 1. Common Table Expressions (CTE)
```sql
-- Example: Using CTE for complex queries
WITH upcoming_meetings AS (
    SELECT m.*
    FROM meetings m
    WHERE start_time > NOW()
),
participant_counts AS (
    SELECT meeting_id,
           COUNT(*) as participant_count
    FROM meeting_participants
    GROUP BY meeting_id
)
SELECT um.*,
       COALESCE(pc.participant_count, 0) as participants
FROM upcoming_meetings um
LEFT JOIN participant_counts pc ON um.id = pc.meeting_id
ORDER BY um.start_time;
```

### 2. Window Functions
```sql
-- Example: Using window functions
SELECT m.*,
       COUNT(*) OVER (
           PARTITION BY DATE_TRUNC('day', start_time)
       ) as meetings_per_day,
       ROW_NUMBER() OVER (
           PARTITION BY created_by
           ORDER BY start_time
       ) as user_meeting_number
FROM meetings m;

-- Example: Moving averages
SELECT DATE_TRUNC('day', start_time) as date,
       COUNT(*) as meeting_count,
       AVG(COUNT(*)) OVER (
           ORDER BY DATE_TRUNC('day', start_time)
           ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ) as seven_day_average
FROM meetings
GROUP BY DATE_TRUNC('day', start_time)
ORDER BY date;
```

## Performance Monitoring

### 1. Slow Query Logging
```sql
-- Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = '1000';  -- Log queries over 1 second

-- Example: Analyzing slow queries
SELECT pid,
       now() - pg_stat_activity.query_start AS duration,
       query,
       state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '1 second';
```

### 2. Query Plan Analysis
```python
# Example: Using SQLAlchemy for query analysis
from sqlalchemy import create_engine, text

def analyze_query(query_text):
    """Analyze query performance."""
    with engine.connect() as conn:
        # Get query plan
        result = conn.execute(
            text(f"EXPLAIN ANALYZE {query_text}")
        )
        plan = '\n'.join([row[0] for row in result])
        
        # Parse and analyze plan
        total_cost = None
        execution_time = None
        for line in plan.split('\n'):
            if 'Total Cost:' in line:
                total_cost = float(
                    line.split(':')[1].split('..')[1]
                )
            if 'Execution Time:' in line:
                execution_time = float(
                    line.split(':')[1].strip(' ms')
                )
        
        return {
            'plan': plan,
            'total_cost': total_cost,
            'execution_time': execution_time
        }
```

## Best Practices

### 1. Query Design
- Use appropriate indexes
- Avoid SELECT *
- Use prepared statements
- Optimize JOINs
- Use appropriate pagination

### 2. Performance Tuning
- Monitor query performance
- Use query planning tools
- Optimize common patterns
- Regular maintenance
- Cache when appropriate

### 3. Resource Management
- Connection pooling
- Statement timeouts
- Transaction management
- Resource limits
- Query cancellation

## Common Pitfalls

### 1. N+1 Query Problem
```python
# Bad: N+1 queries
meetings = Meeting.query.all()
for meeting in meetings:
    participants = meeting.participants.all()  # Additional query per meeting

# Good: Eager loading
meetings = Meeting.query.options(
    joinedload('participants')
).all()
```

### 2. Inefficient Queries
```sql
-- Bad: Using functions in WHERE clause
SELECT *
FROM users
WHERE EXTRACT(YEAR FROM created_at) = 2024;

-- Good: Using indexed columns directly
SELECT *
FROM users
WHERE created_at >= '2024-01-01'
  AND created_at < '2025-01-01';
```

## Next Steps
After mastering query optimization, proceed to:
1. Database Maintenance (4_database_maintenance.md) 