# Network Policies

This document describes the network policies implemented for secure communication between services.

## Overview

Network policies are implemented using Kubernetes NetworkPolicy resources to control traffic flow between pods.

## Service Policies

### Frontend Network Policy
```yaml
# frontend-policy.yaml
spec:
  podSelector:
    matchLabels:
      app: meeting-app-frontend
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: ingress-nginx
    ports:
    - protocol: TCP
      port: 3000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: meeting-app
    ports:
    - protocol: TCP
      port: 5000
    - protocol: TCP
      port: 3001
```

### Backend Network Policy
```yaml
# flask-backend-policy.yaml
spec:
  podSelector:
    matchLabels:
      app: meeting-app
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: meeting-app-frontend
    ports:
    - protocol: TCP
      port: 5000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### WebSocket Network Policy
```yaml
# node-backend-policy.yaml
spec:
  podSelector:
    matchLabels:
      app: meeting-app
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: meeting-app-frontend
    ports:
    - protocol: TCP
      port: 3001
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

### Database Network Policy
```yaml
# postgres-policy.yaml
spec:
  podSelector:
    matchLabels:
      app: postgres
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: meeting-app
    ports:
    - protocol: TCP
      port: 5432
```

### Redis Network Policy
```yaml
# redis-policy.yaml
spec:
  podSelector:
    matchLabels:
      app: redis
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: meeting-app
    ports:
    - protocol: TCP
      port: 6379
```

## DNS Access

All services have egress access to kube-dns for service discovery:
```yaml
egress:
- to:
  - namespaceSelector:
      matchLabels:
        kubernetes.io/metadata.name: kube-system
    podSelector:
      matchLabels:
        k8s-app: kube-dns
  ports:
  - protocol: UDP
    port: 53
  - protocol: TCP
    port: 53
```

## Monitoring Access

Prometheus has access to scrape metrics from all application services:
```yaml
spec:
  podSelector:
    matchLabels:
      app: prometheus
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: grafana
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: meeting-app
    - podSelector:
        matchLabels:
          app: meeting-app-frontend
```

## Logging Access

Filebeat has access to forward logs to Logstash:
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
``` 