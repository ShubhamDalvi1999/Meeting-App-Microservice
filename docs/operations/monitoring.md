# Monitoring Stack

This document describes the monitoring setup for the Meeting App using Prometheus and Grafana.

## Components

1. Prometheus
   - Version: v2.40.0
   - Port: 9090
   - Role: Metrics collection and storage

2. Grafana
   - Version: 9.3.0
   - Port: 3000
   - Role: Metrics visualization

## Metrics Collection

### Service Endpoints

```yaml
scrape_configs:
  - job_name: 'meeting-app-backend'
    static_configs:
    - targets: ['meeting-app:5000']

  - job_name: 'meeting-app-websocket'
    static_configs:
    - targets: ['meeting-app:3001']

  - job_name: 'meeting-app-frontend'
    static_configs:
    - targets: ['meeting-app-frontend:3000']
```

### Kubernetes Metrics

```yaml
scrape_configs:
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
    - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token

  - job_name: 'kubernetes-nodes'
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    kubernetes_sd_configs:
    - role: node

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
    - role: pod
```

## Resource Allocation

### Prometheus
```yaml
resources:
  limits:
    cpu: "1000m"
    memory: "1Gi"
  requests:
    cpu: "500m"
    memory: "512Mi"
```

### Grafana
```yaml
resources:
  limits:
    cpu: "500m"
    memory: "512Mi"
  requests:
    cpu: "200m"
    memory: "256Mi"
```

## Access

### Prometheus
- Internal: `http://prometheus:9090`
- Authentication: None (internal only)
- Network Policy: Allow ingress from Grafana

### Grafana
- External: `http://localhost:3000`
- Default Credentials:
  - Username: admin
  - Password: admin123 (change on first login)
- Network Policy: Allow ingress from ingress-nginx

## Dashboards

### 1. Application Overview
- Service health status
- Request rates
- Error rates
- Response times

### 2. Backend Metrics
- API endpoints performance
- Database connections
- Cache hit rates
- WebSocket connections

### 3. Frontend Metrics
- Page load times
- Client-side errors
- WebSocket connection status
- Resource usage

### 4. Infrastructure
- Node metrics
- Pod metrics
- Network traffic
- Resource utilization

## Alerts

### Service Health
```yaml
groups:
- name: service.rules
  rules:
  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      description: "{{ $labels.job }} service is down"
```

### Performance
```yaml
groups:
- name: performance.rules
  rules:
  - alert: HighLatency
    expr: http_request_duration_seconds > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      description: "High latency for {{ $labels.endpoint }}"
```

## Retention

### Prometheus
- Storage: EmptyDir (non-persistent for development)
- Retention: 15 days
- Storage size: Limited by pod memory

### Grafana
- Storage: EmptyDir (non-persistent for development)
- Dashboard configs: ConfigMap
- Data source configs: ConfigMap

## Health Checks

### Prometheus
```yaml
livenessProbe:
  httpGet:
    path: /-/healthy
    port: 9090
  initialDelaySeconds: 30
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /-/ready
    port: 9090
  initialDelaySeconds: 30
  periodSeconds: 15
```

### Grafana
```yaml
readinessProbe:
  httpGet:
    path: /api/health
    port: 3000
  initialDelaySeconds: 30
  periodSeconds: 10

livenessProbe:
  httpGet:
    path: /api/health
    port: 3000
  initialDelaySeconds: 60
  periodSeconds: 30
``` 