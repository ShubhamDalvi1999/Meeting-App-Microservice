# 4. Database Maintenance

## Overview
This document covers database maintenance strategies in our meeting management system. Regular maintenance is crucial for ensuring optimal performance, data integrity, and system reliability.

## Routine Maintenance

### 1. VACUUM Operations
```sql
-- Example: Manual VACUUM
VACUUM ANALYZE meetings;

-- Example: VACUUM FULL
VACUUM FULL meetings;

-- Example: Automatic VACUUM settings
ALTER SYSTEM SET autovacuum = on;
ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;
ALTER SYSTEM SET autovacuum_analyze_threshold = 50;
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.2;
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.1;
```

### 2. Index Maintenance
```sql
-- Example: Rebuild index
REINDEX INDEX idx_meetings_time_range;

-- Example: Check index usage
SELECT schemaname,
       relname,
       indexrelname,
       idx_scan,
       idx_tup_read,
       idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public';

-- Example: Remove unused indexes
DROP INDEX IF EXISTS idx_unused_index;
```

## Database Monitoring

### 1. Performance Monitoring
```python
# Example: Database monitoring class
class DatabaseMonitor:
    def __init__(self, engine):
        self.engine = engine

    def check_connection_count(self):
        """Monitor active connections."""
        query = """
            SELECT count(*) as active_connections
            FROM pg_stat_activity
            WHERE state = 'active'
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.scalar()

    def check_table_bloat(self):
        """Check table bloat."""
        query = """
            SELECT schemaname,
                   tablename,
                   ROUND(CASE WHEN otta=0 THEN 0.0
                        ELSE sml.relpages/otta::numeric END,1) AS bloat_ratio
            FROM (
                SELECT schemaname, tablename, cc.reltuples, cc.relpages, bs,
                    CEIL((cc.reltuples*((datahdr+ma-
                        (CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+nullhdr2+4)/bs)::numeric) AS otta
                FROM (
                    SELECT ma,bs,schemaname,tablename,
                        (datawidth+(hdr+ma-(case when hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric AS datahdr,
                        (maxfracsum*(nullhdr+ma-(case when nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
                    FROM (
                        SELECT schemaname, tablename, hdr, ma, bs,
                            SUM((1-null_frac)*avg_width) AS datawidth,
                            MAX(null_frac) AS maxfracsum
                        FROM pg_stats s2
                        JOIN pg_class cc ON cc.relname = s2.tablename
                        JOIN pg_namespace nn ON cc.relnamespace = nn.oid
                            AND nn.nspname = s2.schemaname
                        GROUP BY 1,2,3,4,5
                    ) AS foo
                ) AS rs
            JOIN pg_class cc ON cc.relname = rs.tablename
            JOIN pg_namespace nn ON cc.relnamespace = nn.oid
                AND nn.nspname = rs.schemaname AND nn.nspname <> 'information_schema'
            ) AS sml
            WHERE sml.relpages - otta > 128
            ORDER BY bloat_ratio DESC
        """
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(query))]

    def check_long_running_queries(self, threshold_seconds=300):
        """Monitor long-running queries."""
        query = """
            SELECT pid,
                   now() - pg_stat_activity.query_start AS duration,
                   query,
                   state
            FROM pg_stat_activity
            WHERE state != 'idle'
              AND (now() - pg_stat_activity.query_start) > interval '%s seconds'
        """ % threshold_seconds
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(query))]
```

### 2. Space Management
```python
# Example: Space monitoring class
class SpaceMonitor:
    def __init__(self, engine):
        self.engine = engine

    def check_database_size(self):
        """Monitor database size."""
        query = """
            SELECT pg_size_pretty(pg_database_size(current_database()))
            AS db_size
        """
        with self.engine.connect() as conn:
            return conn.execute(text(query)).scalar()

    def check_table_sizes(self):
        """Monitor table sizes."""
        query = """
            SELECT relname AS table_name,
                   pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
                   pg_size_pretty(pg_table_size(relid)) AS table_size,
                   pg_size_pretty(pg_indexes_size(relid)) AS index_size
            FROM pg_catalog.pg_statio_user_tables
            ORDER BY pg_total_relation_size(relid) DESC
        """
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(query))]

    def check_bloated_tables(self):
        """Check for bloated tables."""
        query = """
            SELECT schemaname,
                   tablename,
                   pg_size_pretty(wastedbytes) AS bloat_size
            FROM (
                SELECT schemaname,
                       tablename,
                       CASE WHEN tblpages - est_tblpages_ff > 0
                            THEN (tblpages - est_tblpages_ff)*bs
                            ELSE 0
                       END AS wastedbytes
                FROM (
                    -- Calculate estimated pages
                ) AS inner_query
            ) AS outer_query
            WHERE wastedbytes > 0
            ORDER BY wastedbytes DESC
        """
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(text(query))]
```

## Backup and Recovery

### 1. Backup Strategies
```python
# Example: Backup management class
class BackupManager:
    def __init__(self, config):
        self.config = config

    def create_backup(self):
        """Create database backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backup_{timestamp}.sql"
        
        command = f"""
            pg_dump -h {self.config.host} 
                    -U {self.config.user} 
                    -d {self.config.database} 
                    -F c 
                    -f {backup_file}
        """
        subprocess.run(command, shell=True, check=True)
        return backup_file

    def restore_backup(self, backup_file):
        """Restore database from backup."""
        command = f"""
            pg_restore -h {self.config.host} 
                      -U {self.config.user} 
                      -d {self.config.database} 
                      -c 
                      {backup_file}
        """
        subprocess.run(command, shell=True, check=True)

    def list_backups(self):
        """List available backups."""
        return glob.glob("backup_*.sql")

    def cleanup_old_backups(self, days_to_keep=30):
        """Remove old backups."""
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        for backup in self.list_backups():
            backup_time = datetime.strptime(
                backup.split('_')[1].split('.')[0],
                '%Y%m%d_%H%M%S'
            )
            if backup_time < cutoff:
                os.remove(backup)
```

### 2. Recovery Procedures
```python
# Example: Recovery management class
class RecoveryManager:
    def __init__(self, config):
        self.config = config

    def point_in_time_recovery(self, target_time):
        """Perform point-in-time recovery."""
        recovery_conf = f"""
            restore_command = 'cp /path/to/archive/%f %p'
            recovery_target_time = '{target_time}'
            recovery_target_action = 'promote'
        """
        # Write recovery.conf and restart database
        
    def verify_recovery(self):
        """Verify database recovery."""
        queries = [
            "SELECT COUNT(*) FROM users",
            "SELECT COUNT(*) FROM meetings",
            "SELECT MAX(created_at) FROM meetings"
        ]
        results = {}
        with create_engine(self.config.url).connect() as conn:
            for query in queries:
                results[query] = conn.execute(text(query)).scalar()
        return results

    def failover_to_replica(self):
        """Perform failover to replica."""
        # Promote replica to primary
        command = "pg_ctl promote -D /path/to/data"
        subprocess.run(command, shell=True, check=True)
```

## Best Practices

### 1. Maintenance Schedule
- Regular VACUUM operations
- Index maintenance
- Statistics updates
- Backup verification
- Performance monitoring

### 2. Monitoring Strategy
- Set up alerts
- Monitor performance
- Track space usage
- Check error logs
- Monitor connections

### 3. Backup Strategy
- Regular backups
- Verify backups
- Multiple backup types
- Secure storage
- Test recovery

## Common Pitfalls

### 1. Poor Maintenance
```python
# Bad: No regular maintenance
# System degrades over time

# Good: Scheduled maintenance
@scheduled_task.periodic_task(run_every=timedelta(days=1))
def perform_daily_maintenance():
    """Perform daily maintenance tasks."""
    vacuum_analyze_tables()
    update_statistics()
    check_index_usage()
    monitor_table_bloat()
```

### 2. Inadequate Monitoring
```python
# Bad: No monitoring
# Problems discovered too late

# Good: Proactive monitoring
def monitor_database_health():
    """Monitor database health."""
    metrics = {
        'connections': check_connection_count(),
        'long_queries': check_long_running_queries(),
        'table_bloat': check_table_bloat(),
        'space_usage': check_database_size()
    }
    
    for metric, value in metrics.items():
        if exceeds_threshold(metric, value):
            send_alert(f"Database metric {metric} exceeded threshold")
```

## Next Steps
After mastering database maintenance, you have completed the database documentation series! You can now:
1. Review all documentation
2. Implement maintenance procedures
3. Set up monitoring
4. Plan backup strategies
5. Share knowledge with team 