# Management Scripts Documentation

## Overview
The management scripts provide a collection of utilities for deploying, managing, and maintaining the application infrastructure. These scripts automate common tasks and ensure consistent operations.

## Available Scripts

### 1. deploy-all.sh
**Purpose**: Deploy the entire application stack

**Features**:
- Namespace creation
- Secret management
- Component deployment
- Health verification

**Usage**:
```bash
./deploy-all.sh
```

**Flow**:
1. Create namespaces
2. Apply secrets
3. Deploy PostgreSQL
4. Deploy backend services
5. Deploy frontend
6. Deploy monitoring
7. Deploy logging
8. Apply network policies
9. Configure ingress
10. Verify deployment

### 2. deploy-monitoring.sh
**Purpose**: Deploy monitoring stack

**Features**:
- Prometheus deployment
- Grafana setup
- Alert configuration
- Dashboard import

**Usage**:
```bash
./deploy-monitoring.sh
```

**Flow**:
1. Create monitoring namespace
2. Deploy Prometheus
3. Deploy Grafana
4. Import dashboards
5. Configure alerts

### 3. deploy-logging.sh
**Purpose**: Deploy logging stack

**Features**:
- ELK stack deployment
- Filebeat setup
- Log shipping configuration
- Index management

**Usage**:
```bash
./deploy-logging.sh
```

**Flow**:
1. Create logging namespace
2. Deploy Elasticsearch
3. Deploy Logstash
4. Deploy Kibana
5. Configure Filebeat

### 4. cleanup.sh
**Purpose**: Remove all deployed resources

**Features**:
- Resource cleanup
- Namespace removal
- Volume cleanup
- Configuration reset

**Usage**:
```bash
./cleanup.sh
```

**Flow**:
1. Confirm deletion
2. Remove deployments
3. Remove services
4. Delete PVCs
5. Remove namespaces

### 5. update-rollback.sh
**Purpose**: Manage application updates and rollbacks

**Features**:
- Version updates
- Rollback support
- Health checking
- Status monitoring

**Usage**:
```bash
./update-rollback.sh [update|rollback] [service] [options]
```

**Examples**:
```bash
# Update frontend
./update-rollback.sh update frontend -i myregistry/frontend:v2

# Rollback backend
./update-rollback.sh rollback flask-backend -r 1
```

### 6. scale.sh
**Purpose**: Manage application scaling

**Features**:
- Manual scaling
- Auto-scaling configuration
- Resource adjustment
- Performance monitoring

**Usage**:
```bash
./scale.sh [manual|auto] [service] [options]
```

**Examples**:
```bash
# Manual scaling
./scale.sh manual frontend -r 3

# Auto-scaling
./scale.sh auto flask-backend --min 2 --max 5 --cpu 75 --memory 85
```

### 7. monitor-debug.sh
**Purpose**: Monitor and debug application components

**Features**:
- Log viewing
- Resource monitoring
- Event tracking
- Status checking

**Usage**:
```bash
./monitor-debug.sh [command] [service] [options]
```

**Examples**:
```bash
# View logs
./monitor-debug.sh logs frontend -f

# Check metrics
./monitor-debug.sh metrics node-backend
```

### 8. backup-restore.sh
**Purpose**: Manage database backups and restores

**Features**:
- Database backup
- Backup restoration
- Scheduled backups
- Verification

**Usage**:
```bash
./backup-restore.sh [backup|restore] [options]
```

**Examples**:
```bash
# Create backup
./backup-restore.sh backup -d myapp -f backup.sql

# Restore backup
./backup-restore.sh restore -d myapp -f backup.sql
```

### 9. manage-secrets.sh
**Purpose**: Manage Kubernetes secrets

**Features**:
- Secret creation
- Secret updates
- Secret rotation
- Access control

**Usage**:
```bash
./manage-secrets.sh [command] [options]
```

**Examples**:
```bash
# Create secret
./manage-secrets.sh create -s my-secret -k api-key -v 12345

# Rotate secret
./manage-secrets.sh rotate -s postgres-secret
```

### 10. manage-certs.sh
**Purpose**: Manage SSL certificates

**Features**:
- Certificate generation
- Certificate renewal
- Let's Encrypt integration
- TLS configuration

**Usage**:
```bash
./manage-certs.sh [command] [options]
```

**Examples**:
```bash
# Generate certificate
./manage-certs.sh generate -d example.com -e admin@example.com

# Renew certificate
./manage-certs.sh renew -s tls-secret
```

## Common Operations

### 1. Initial Deployment
```bash
# Deploy entire stack
./deploy-all.sh

# Verify deployment
./monitor-debug.sh status
```

### 2. Update Application
```bash
# Update service
./update-rollback.sh update frontend -i new-image:tag

# Monitor rollout
./monitor-debug.sh events
```

### 3. Backup Database
```bash
# Create backup
./backup-restore.sh backup -d myapp

# Verify backup
ls -l backups/
```

### 4. Scale Services
```bash
# Manual scaling
./scale.sh manual frontend -r 5

# Configure auto-scaling
./scale.sh auto flask-backend --min 2 --max 5
```

## Best Practices

### 1. Script Usage
- Review parameters before execution
- Test in development first
- Monitor script execution
- Keep logs for audit

### 2. Maintenance
- Regular script updates
- Parameter validation
- Error handling
- Documentation updates

### 3. Security
- Access control
- Secret handling
- Audit logging
- Secure communication

## Troubleshooting

### 1. Common Issues
- Permission errors
- Resource constraints
- Network connectivity
- Configuration errors

### 2. Resolution Steps
1. Check logs
2. Verify permissions
3. Review configurations
4. Test connectivity

### 3. Prevention
- Regular testing
- Resource monitoring
- Configuration validation
- Team training 