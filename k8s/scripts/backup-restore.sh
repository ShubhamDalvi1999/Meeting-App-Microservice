#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [backup|restore] [options]"
    echo
    echo "Commands:"
    echo "  backup   Create a backup of the PostgreSQL database"
    echo "  restore  Restore a backup to the PostgreSQL database"
    echo
    echo "Options:"
    echo "  -f, --file      Backup file name (default: backup-YYYY-MM-DD.sql)"
    echo "  -n, --namespace Namespace (default: app)"
    echo "  -d, --database  Database name (required)"
    echo
    echo "Examples:"
    echo "  $0 backup -d myapp -f custom-backup.sql"
    echo "  $0 restore -d myapp -f backup-2023-12-25.sql"
    exit 1
}

# Function to get pod name
get_pod_name() {
    local namespace=${1:-app}
    kubectl get pods -n $namespace -l app=postgres -o jsonpath="{.items[0].metadata.name}"
}

# Function to create backup
create_backup() {
    local database=$1
    local backup_file=$2
    local namespace=${3:-app}
    
    local pod=$(get_pod_name $namespace)
    if [ -z "$pod" ]; then
        echo "Error: PostgreSQL pod not found in namespace $namespace"
        exit 1
    fi
    
    echo "Creating backup of database $database to file $backup_file"
    
    # Create backup directory if it doesn't exist
    mkdir -p backups
    
    # Get database credentials from secret
    local db_user=$(kubectl get secret postgres-secret -n $namespace -o jsonpath="{.data.POSTGRES_USER}" | base64 --decode)
    local db_password=$(kubectl get secret postgres-secret -n $namespace -o jsonpath="{.data.POSTGRES_PASSWORD}" | base64 --decode)
    
    # Create backup
    kubectl exec -n $namespace $pod -- \
        pg_dump -U $db_user -d $database \
        | gzip > "backups/$backup_file.gz"
    
    if [ $? -eq 0 ]; then
        echo "Backup completed successfully"
        echo "Backup file: backups/$backup_file.gz"
    else
        echo "Error: Backup failed"
        exit 1
    fi
}

# Function to restore backup
restore_backup() {
    local database=$1
    local backup_file=$2
    local namespace=${3:-app}
    
    local pod=$(get_pod_name $namespace)
    if [ -z "$pod" ]; then
        echo "Error: PostgreSQL pod not found in namespace $namespace"
        exit 1
    fi
    
    if [ ! -f "backups/$backup_file.gz" ]; then
        echo "Error: Backup file backups/$backup_file.gz not found"
        exit 1
    fi
    
    echo "Restoring database $database from file $backup_file"
    
    # Get database credentials from secret
    local db_user=$(kubectl get secret postgres-secret -n $namespace -o jsonpath="{.data.POSTGRES_USER}" | base64 --decode)
    local db_password=$(kubectl get secret postgres-secret -n $namespace -o jsonpath="{.data.POSTGRES_PASSWORD}" | base64 --decode)
    
    # Drop existing connections
    kubectl exec -n $namespace $pod -- \
        psql -U $db_user -d postgres -c "
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '$database'
            AND pid <> pg_backend_pid();"
    
    # Drop and recreate database
    kubectl exec -n $namespace $pod -- \
        psql -U $db_user -d postgres -c "DROP DATABASE IF EXISTS $database;"
    kubectl exec -n $namespace $pod -- \
        psql -U $db_user -d postgres -c "CREATE DATABASE $database;"
    
    # Restore backup
    gunzip < "backups/$backup_file.gz" | \
        kubectl exec -i -n $namespace $pod -- \
        psql -U $db_user -d $database
    
    if [ $? -eq 0 ]; then
        echo "Restore completed successfully"
    else
        echo "Error: Restore failed"
        exit 1
    fi
}

# Parse command line arguments
if [ $# -lt 1 ]; then
    usage
fi

command=$1
shift

namespace="app"
database=""
backup_file="backup-$(date +%Y-%m-%d).sql"

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            namespace="$2"
            shift 2
            ;;
        -d|--database)
            database="$2"
            shift 2
            ;;
        -f|--file)
            backup_file="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

if [ -z "$database" ]; then
    echo "Error: Database name is required"
    usage
fi

case $command in
    backup)
        create_backup $database $backup_file $namespace
        ;;
    restore)
        read -p "Warning: This will overwrite the existing database. Continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            restore_backup $database $backup_file $namespace
        else
            echo "Operation cancelled"
            exit 1
        fi
        ;;
    *)
        echo "Unknown command: $command"
        usage
        ;;
esac 