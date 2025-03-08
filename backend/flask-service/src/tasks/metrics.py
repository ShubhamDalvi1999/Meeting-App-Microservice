import logging
import json
import os
import platform
import time
from datetime import datetime, timezone
from sqlalchemy import text
from flask import current_app
from ..database import db
from ..models.meeting import Meeting

logger = logging.getLogger(__name__)

def update_system_metrics():
    """
    Collect and store system metrics for monitoring
    """
    try:
        logger.info("Starting metrics collection")
        start_time = time.time()
        
        with current_app.app_context():
            metrics = {}
            
            # DB metrics
            db_metrics = collect_database_metrics()
            if db_metrics:
                metrics.update(db_metrics)
            
            # Application metrics
            app_metrics = collect_application_metrics()
            if app_metrics:
                metrics.update(app_metrics)
            
            # System metrics
            sys_metrics = collect_system_metrics()
            if sys_metrics:
                metrics.update(sys_metrics)
            
            # Store metrics in Redis
            redis_client = current_app.extensions.get('redis')
            if redis_client:
                # Add timestamp
                metrics['timestamp'] = datetime.now(timezone.utc).isoformat()
                metrics['collection_duration_ms'] = int((time.time() - start_time) * 1000)
                
                # Store latest metrics
                for key, value in metrics.items():
                    redis_client.hset('metrics:system:latest', key, _serialize_value(value))
                
                # Set expiry for latest metrics
                redis_client.expire('metrics:system:latest', 86400)  # 24 hours
                
                # Store historical data points for time-series metrics
                store_time_series_metrics(redis_client, metrics)
                
                logger.info(f"Metrics collection completed in {(time.time() - start_time):.2f} seconds")
                return metrics
            else:
                logger.warning("Redis client not available, metrics not stored")
                return metrics
    
    except Exception as e:
        logger.error(f"Error during metrics collection: {str(e)}")
        return {'error': str(e)}

def _serialize_value(value):
    """Serialize value for Redis storage"""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)

def collect_database_metrics():
    """Collect database metrics"""
    try:
        metrics = {}
        
        # Count active meetings
        active_meetings = Meeting.query.filter(
            Meeting.ended_at.is_(None),
            Meeting.is_cancelled == False
        ).count()
        metrics['active_meetings'] = active_meetings
        
        # Count total meetings
        total_meetings = Meeting.query.count()
        metrics['total_meetings'] = total_meetings
        
        # Count today's meetings
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        todays_meetings = Meeting.query.filter(
            Meeting.start_time >= today
        ).count()
        metrics['todays_meetings'] = todays_meetings
        
        # Get database size (PostgreSQL)
        try:
            db_name = current_app.config.get('SQLALCHEMY_DATABASE_URI').split('/')[-1]
            query = text("""
                SELECT pg_database_size(:db_name) as db_size
            """)
            result = db.session.execute(query, {'db_name': db_name}).first()
            if result:
                metrics['database_size_bytes'] = result.db_size
        except Exception as e:
            logger.warning(f"Could not get database size: {e}")
        
        # Get table statistics
        try:
            query = text("""
                SELECT 
                    relname as table_name,
                    n_live_tup as row_count
                FROM 
                    pg_stat_user_tables
                ORDER BY 
                    n_live_tup DESC
            """)
            results = db.session.execute(query).fetchall()
            table_stats = {r.table_name: r.row_count for r in results}
            metrics['table_row_counts'] = table_stats
        except Exception as e:
            logger.warning(f"Could not get table statistics: {e}")
        
        return metrics
    except Exception as e:
        logger.error(f"Error collecting database metrics: {e}")
        return {}

def collect_application_metrics():
    """Collect application metrics"""
    try:
        metrics = {}
        
        # Application version/build info
        metrics['app_version'] = os.environ.get('APP_VERSION', 'unknown')
        metrics['flask_env'] = current_app.config.get('FLASK_ENV', 'unknown')
        
        # Cache hit ratio if available
        redis_client = current_app.extensions.get('redis')
        if redis_client:
            try:
                # Get cache statistics from Redis INFO
                info = redis_client.info()
                metrics['redis_hit_ratio'] = (info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses'] + 0.001)) * 100
                metrics['redis_used_memory'] = info['used_memory']
                metrics['redis_connected_clients'] = info['connected_clients']
            except Exception as e:
                logger.warning(f"Could not get Redis stats: {e}")
        
        return metrics
    except Exception as e:
        logger.error(f"Error collecting application metrics: {e}")
        return {}

def collect_system_metrics():
    """Collect system metrics"""
    try:
        metrics = {}
        
        # System information
        metrics['python_version'] = platform.python_version()
        metrics['os_name'] = platform.system()
        metrics['os_version'] = platform.version()
        
        # Process information
        metrics['process_id'] = os.getpid()
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process(os.getpid())
            
            # Memory usage for this process
            memory_info = process.memory_info()
            metrics['process_memory_rss'] = memory_info.rss
            metrics['process_memory_vms'] = memory_info.vms
            
            # CPU usage
            metrics['process_cpu_percent'] = process.cpu_percent(interval=0.1)
            metrics['system_cpu_percent'] = psutil.cpu_percent(interval=0.1)
            
            # System memory
            system_memory = psutil.virtual_memory()
            metrics['system_memory_available'] = system_memory.available
            metrics['system_memory_total'] = system_memory.total
            metrics['system_memory_percent'] = system_memory.percent
            
            # Disk usage
            disk_usage = psutil.disk_usage('/')
            metrics['disk_usage_percent'] = disk_usage.percent
            metrics['disk_free'] = disk_usage.free
        except ImportError:
            logger.warning("psutil not available, skipping detailed system metrics")
        
        return metrics
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        return {}

def store_time_series_metrics(redis_client, metrics):
    """Store time-series metrics for historical analysis"""
    try:
        timestamp = int(time.time())
        
        # Define which metrics to track historically
        time_series_metrics = [
            'active_meetings',
            'process_memory_rss',
            'system_cpu_percent',
            'system_memory_percent',
            'redis_hit_ratio'
        ]
        
        # For each metric, store a data point
        for metric_name in time_series_metrics:
            if metric_name in metrics:
                # Store as a sorted set with timestamp as score
                # This allows efficient time range queries
                redis_client.zadd(
                    f'metrics:timeseries:{metric_name}',
                    {f"{timestamp}:{metrics[metric_name]}": timestamp}
                )
                
                # Trim to last 1000 points to avoid unlimited growth
                redis_client.zremrangebyrank(
                    f'metrics:timeseries:{metric_name}',
                    0, -1001
                )
    except Exception as e:
        logger.error(f"Error storing time-series metrics: {e}") 