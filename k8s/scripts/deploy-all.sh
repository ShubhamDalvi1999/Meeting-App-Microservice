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

# Create namespaces if they don't exist
if ! check_resource namespace app; then
    echo "Creating app namespace..."
    kubectl create namespace app
fi

if ! check_resource namespace monitoring; then
    echo "Creating monitoring namespace..."
    kubectl create namespace monitoring
fi

if ! check_resource namespace logging; then
    echo "Creating logging namespace..."
    kubectl create namespace logging
fi

# Apply Secrets
echo "Applying Secrets..."
kubectl apply -f ../secrets.yaml

# Apply Network Policies
echo "Applying Network Policies..."
kubectl apply -f ../network-policies/frontend-policy.yaml
kubectl apply -f ../network-policies/flask-backend-policy.yaml
kubectl apply -f ../network-policies/node-backend-policy.yaml
kubectl apply -f ../network-policies/postgres-policy.yaml
kubectl apply -f ../network-policies/monitoring-policy.yaml
kubectl apply -f ../network-policies/logging-policy.yaml

# Deploy PostgreSQL
echo "Deploying PostgreSQL..."
kubectl apply -f ../postgres-deployment.yaml
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

# Deploy Flask Backend
echo "Deploying Flask Backend..."
kubectl apply -f ../flask-backend-deployment.yaml
wait_for_deployment flask-backend

# Deploy Node.js Backend
echo "Deploying Node.js Backend..."
kubectl apply -f ../node-backend-deployment.yaml
wait_for_deployment node-backend

# Deploy Frontend
echo "Deploying Frontend..."
kubectl apply -f ../frontend-deployment.yaml
wait_for_deployment frontend

# Deploy Monitoring Stack
echo "Deploying Monitoring Stack..."
./deploy-monitoring.sh

# Deploy Logging Stack
echo "Deploying Logging Stack..."
./deploy-logging.sh

# Apply Ingress
echo "Applying Ingress..."
kubectl apply -f ../ingress.yaml

# Apply HPA
echo "Applying Horizontal Pod Autoscaling..."
kubectl apply -f ../hpa.yaml

# Wait for all pods to be ready
echo "Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod -l app=frontend --timeout=300s
kubectl wait --for=condition=ready pod -l app=flask-backend --timeout=300s
kubectl wait --for=condition=ready pod -l app=node-backend --timeout=300s
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s

echo "Application stack deployment complete!"
echo "The application will be available at: http://localhost"
echo "Grafana will be available at: http://localhost:3000"
echo "Kibana will be available at: http://localhost:5601"

echo "To view the status of your pods:"
echo "kubectl get pods -A"

echo "To view the status of your services:"
echo "kubectl get svc -A"

echo "To view the status of your deployments:"
echo "kubectl get deployments -A"

echo "To view the logs of a specific pod:"
echo "kubectl logs <pod-name>"

echo "To port-forward services locally:"
echo "kubectl port-forward svc/frontend 3000:3000"
echo "kubectl port-forward svc/grafana 3000:3000"
echo "kubectl port-forward svc/kibana 5601:5601" 