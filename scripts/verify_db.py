#!/usr/bin/env python
"""
Database connection verification script.
Tests connections to both auth and backend databases.
"""

import os
import sys
from flask import Flask
import psycopg2

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meeting_shared.config import get_config
from meeting_shared.database import init_db, db

def verify_database_connection(service_type='flask'):
    """Verify database connection with current configuration."""
    app = Flask(__name__)
    
    # Get appropriate config based on service type
    if service_type == 'auth':
        config = get_config('auth')
        db_env_var = 'AUTH_DATABASE_URL'
        service_name = 'Auth Service'
        default_url = 'postgresql://postgres:postgres@localhost:5433/auth_db'
    else:
        config = get_config('flask')
        db_env_var = 'DATABASE_URL'
        service_name = 'Flask Service'
        default_url = 'postgresql://dev_user:dev-password-123@localhost:5432/meetingapp'
    
    # Apply configuration
    app.config.from_object(config)
    
    # Override with environment variable if present
    if os.environ.get(db_env_var):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(db_env_var)
    else:
        # Use default URL for local execution
        app.config['SQLALCHEMY_DATABASE_URI'] = default_url
    
    print(f"\n=== Verifying {service_name} Database Connection ===")
    
    # Print critical config values (sanitized)
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if '://' in db_url:
        # Sanitize credentials in URL
        parts = db_url.split('://')
        if '@' in parts[1]:
            credentials_server = parts[1].split('@')
            sanitized_url = f"{parts[0]}://***:***@{credentials_server[1]}"
        else:
            sanitized_url = f"{parts[0]}://***:***@{parts[1]}"
    else:
        sanitized_url = db_url
    
    print(f"Using database: {sanitized_url}")
    
    # Try direct connection with psycopg2
    try:
        # Parse connection string
        if 'postgres' in db_url.lower():
            # Extract connection parameters from URL
            if '://' in db_url:
                # postgresql://username:password@hostname:port/dbname
                parts = db_url.split('://')
                auth_host = parts[1].split('@')
                if len(auth_host) > 1:
                    auth = auth_host[0].split(':')
                    host_port_db = auth_host[1].split('/')
                    host_port = host_port_db[0].split(':')
                    
                    username = auth[0]
                    password = auth[1] if len(auth) > 1 else ''
                    hostname = host_port[0]
                    port = host_port[1] if len(host_port) > 1 else '5432'
                    dbname = host_port_db[1]
                    
                    # Use localhost instead of container names for local execution
                    if hostname in ['postgres', 'auth-db']:
                        hostname = 'localhost'
                        if hostname == 'auth-db':
                            port = '5433'
                    
                    # Connect directly with psycopg2
                    conn = psycopg2.connect(
                        dbname=dbname,
                        user=username,
                        password=password,
                        host=hostname,
                        port=port
                    )
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1')
                    result = cursor.fetchone()[0]
                    print(f"Direct database connection successful, result: {result}")
                    
                    cursor.execute('SELECT version()')
                    version = cursor.fetchone()[0]
                    print(f"Database version: {version}")
                    
                    cursor.close()
                    conn.close()
                    return True
        
        # If direct connection fails or not postgres, try SQLAlchemy
        init_db(app)
        with app.app_context():
            result = db.session.execute('SELECT 1').scalar()
            print(f"SQLAlchemy database connection successful, result: {result}")
            
            # Get database version
            if 'postgres' in db_url.lower():
                version = db.session.execute('SELECT version()').scalar()
                print(f"Database version: {version}")
            elif 'sqlite' in db_url.lower():
                version = db.session.execute('SELECT sqlite_version()').scalar()
                print(f"SQLite version: {version}")
            
            return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if specific service was requested
    service = 'both'
    if len(sys.argv) > 1:
        service = sys.argv[1].lower()
    
    if service in ['both', 'flask']:
        flask_result = verify_database_connection('flask')
    else:
        flask_result = True
        
    if service in ['both', 'auth']:
        auth_result = verify_database_connection('auth')
    else:
        auth_result = True
    
    # Exit with appropriate status code
    if not (flask_result and auth_result):
        print("\n❌ Database verification failed")
        sys.exit(1)
    else:
        print("\n✅ All database connections verified successfully")
        sys.exit(0) 