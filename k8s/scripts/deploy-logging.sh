#!/bin/bash

# Function to check if a resource exists
check_resource() {
    local resource_type=$1
    local resource_name=$2
    kubectl get $resource_type $resource_name &> /dev/null
}

# Function to wait for a deployment to be ready
wait_for_deployment() {
    local deployment_name=$1
    echo "Waiting for deployment $deployment_name to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/$deployment_name
}

# Create namespace if it doesn't exist
if ! check_resource namespace logging; then
    echo "Creating logging namespace..."
    kubectl create namespace logging
fi

# Apply ConfigMaps
echo "Applying ConfigMaps..."
kubectl apply -f ../logging/elasticsearch-deployment.yaml
kubectl apply -f ../logging/logstash-deployment.yaml
kubectl apply -f ../logging/filebeat-daemonset.yaml

# Apply Network Policies
echo "Applying Network Policies..."
kubectl apply -f ../network-policies/logging-policy.yaml

# Deploy Elasticsearch
echo "Deploying Elasticsearch..."
kubectl apply -f ../logging/elasticsearch-deployment.yaml
wait_for_deployment elasticsearch

# Deploy Logstash
echo "Deploying Logstash..."
kubectl apply -f ../logging/logstash-deployment.yaml
wait_for_deployment logstash

# Deploy Kibana
echo "Deploying Kibana..."
kubectl apply -f ../logging/kibana-deployment.yaml
wait_for_deployment kibana

# Deploy Filebeat
echo "Deploying Filebeat..."
kubectl apply -f ../logging/filebeat-daemonset.yaml

# Wait for all pods to be ready
echo "Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod -l app=elasticsearch --timeout=300s
kubectl wait --for=condition=ready pod -l app=logstash --timeout=300s
kubectl wait --for=condition=ready pod -l app=kibana --timeout=300s
kubectl wait --for=condition=ready pod -l app=filebeat --timeout=300s

echo "Logging stack deployment complete!"
echo "Kibana will be available at: http://localhost:5601"
echo "To port-forward Kibana: kubectl port-forward svc/kibana 5601:5601" 