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
if ! check_resource namespace monitoring; then
    echo "Creating monitoring namespace..."
    kubectl create namespace monitoring
fi

# Apply ConfigMaps
echo "Applying ConfigMaps..."
kubectl apply -f ../monitoring/prometheus-config.yaml

# Apply Network Policies
echo "Applying Network Policies..."
kubectl apply -f ../network-policies/monitoring-policy.yaml

# Deploy Prometheus
echo "Deploying Prometheus..."
kubectl apply -f ../monitoring/prometheus-deployment.yaml
wait_for_deployment prometheus

# Deploy Grafana
echo "Deploying Grafana..."
kubectl apply -f ../monitoring/grafana-deployment.yaml
wait_for_deployment grafana

# Wait for all pods to be ready
echo "Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod -l app=prometheus --timeout=300s
kubectl wait --for=condition=ready pod -l app=grafana --timeout=300s

echo "Monitoring stack deployment complete!"
echo "Grafana will be available at: http://localhost:3000"
echo "Prometheus will be available at: http://localhost:9090"
echo "To port-forward Grafana: kubectl port-forward svc/grafana 3000:3000"
echo "To port-forward Prometheus: kubectl port-forward svc/prometheus 9090:9090"

# Import default dashboards
echo "Importing default dashboards..."
kubectl exec -it $(kubectl get pods -l app=grafana -o jsonpath="{.items[0].metadata.name}") -- \
  grafana-cli plugins install grafana-kubernetes-app

echo "Default dashboards have been imported."
echo "You can now log in to Grafana with the default credentials:"
echo "Username: admin"
echo "Password: admin"
echo "Please change the password after your first login." 