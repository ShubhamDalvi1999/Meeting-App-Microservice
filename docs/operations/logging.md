# Logging Stack

This document describes the logging setup for the Meeting App using Filebeat, Logstash, and Elasticsearch.

## Components

1. Filebeat
   - Version: 7.17.0
   - Role: Log collection and forwarding
   - Deployment: DaemonSet on each node

2. Logstash
   - Version: 7.17.0
   - Port: 5044 (Beats input)
   - Role: Log processing and transformation

3. Elasticsearch
   - Version: 7.17.0
   - Ports:
     - 9200 (HTTP)
     - 9300 (Transport)
   - Role: Log storage and indexing

## Log Collection

### Application Logs

#### Backend Service
```yaml
filebeat.inputs:
- type: container
  paths:
    - /var/log/containers/meeting-app-*.log
  processors:
    - add_kubernetes_metadata:
        host: ${NODE_NAME}
        matchers:
        - logs_path:
            logs_path: "/var/log/containers/"
```

#### Frontend Service
```yaml
filebeat.inputs:
- type: container
  paths:
    - /var/log/containers/meeting-app-frontend-*.log
  processors:
    - add_kubernetes_metadata:
        host: ${NODE_NAME}
        matchers:
        - logs_path:
            logs_path: "/var/log/containers/"
```

### System Logs
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/syslog
    - /var/log/messages
```

## Log Processing

### Logstash Pipeline

#### Input Configuration
```yaml
input {
  beats {
    port => 5044
    ssl => false
  }
}
```

#### Filter Configuration
```yaml
filter {
  if [kubernetes][container][name] =~ "meeting-app" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:log_level} %{GREEDYDATA:log_message}" }
    }
    date {
      match => [ "timestamp", "ISO8601" ]
      target => "@timestamp"
    }
  }
}
```

#### Output Configuration
```yaml
output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "meeting-app-%{+YYYY.MM.dd}"
  }
}
```

## Resource Allocation

### Filebeat
```yaml
resources:
  limits:
    cpu: "200m"
    memory: "256Mi"
  requests:
    cpu: "100m"
    memory: "128Mi"
```

### Logstash
```yaml
resources:
  limits:
    cpu: "1000m"
    memory: "1Gi"
  requests:
    cpu: "500m"
    memory: "512Mi"
```

### Elasticsearch
```yaml
resources:
  limits:
    cpu: "2000m"
    memory: "2Gi"
  requests:
    cpu: "1000m"
    memory: "1Gi"
```

## Log Retention

### Development Environment
- Retention period: 7 days
- Storage: EmptyDir (non-persistent)
- Index lifecycle: Delete after retention period

### Production Environment
- Retention period: 30 days
- Storage: PersistentVolume
- Index lifecycle: 
  - Hot: 0-2 days
  - Warm: 3-7 days
  - Cold: 8-30 days
  - Delete: After 30 days

## Health Checks

### Filebeat
```yaml
livenessProbe:
  exec:
    command:
      - filebeat
      - test
      - config
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Logstash
```yaml
livenessProbe:
  httpGet:
    path: /
    port: 9600
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Elasticsearch
```yaml
readinessProbe:
  httpGet:
    path: /_cluster/health
    port: 9200
  initialDelaySeconds: 30
  periodSeconds: 10

livenessProbe:
  httpGet:
    path: /_cluster/health
    port: 9200
  initialDelaySeconds: 60
  periodSeconds: 30
```

## Log Access

### Kibana
- URL: http://localhost:5601
- Default credentials:
  - Username: elastic
  - Password: changeme (change on first login)
- Features:
  - Log visualization
  - Search and filtering
  - Dashboard creation
  - Saved searches

### Direct Elasticsearch Access
- Internal: http://elasticsearch:9200
- External: http://localhost:9200
- Authentication required for production

## Network Policies

### Filebeat
```yaml
spec:
  podSelector:
    matchLabels:
      app: filebeat
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: logstash
    ports:
    - protocol: TCP
      port: 5044
```

### Logstash
```yaml
spec:
  podSelector:
    matchLabels:
      app: logstash
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: filebeat
    ports:
    - protocol: TCP
      port: 5044
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: elasticsearch
    ports:
    - protocol: TCP
      port: 9200
```

### Elasticsearch
```yaml
spec:
  podSelector:
    matchLabels:
      app: elasticsearch
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: logstash
    ports:
    - protocol: TCP
      port: 9200
  - from:
    - podSelector:
        matchLabels:
          app: kibana
    ports:
    - protocol: TCP
      port: 9200
``` 