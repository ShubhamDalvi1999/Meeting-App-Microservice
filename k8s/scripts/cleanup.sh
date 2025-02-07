#!/bin/bash

# Function to confirm deletion
confirm_deletion() {
    read -p "Are you sure you want to delete all resources? This action cannot be undone. (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 1
    fi
}

# Function to delete resources with a namespace
delete_namespace_resources() {
    local namespace=$1
    echo "Deleting resources in namespace: $namespace"
    
    # Delete deployments
    kubectl delete deployments --all -n $namespace
    
    # Delete services
    kubectl delete services --all -n $namespace
    
    # Delete pods
    kubectl delete pods --all -n $namespace
    
    # Delete configmaps
    kubectl delete configmaps --all -n $namespace
    
    # Delete secrets
    kubectl delete secrets --all -n $namespace
    
    # Delete HPA
    kubectl delete hpa --all -n $namespace
    
    # Delete PVCs
    kubectl delete pvc --all -n $namespace
    
    # Delete the namespace itself
    kubectl delete namespace $namespace
}

# Main cleanup process
echo "Starting cleanup process..."
confirm_deletion

# Delete Ingress resources
echo "Deleting Ingress resources..."
kubectl delete -f ../ingress.yaml

# Delete Network Policies
echo "Deleting Network Policies..."
kubectl delete -f ../network-policies/frontend-policy.yaml
kubectl delete -f ../network-policies/flask-backend-policy.yaml
kubectl delete -f ../network-policies/node-backend-policy.yaml
kubectl delete -f ../network-policies/postgres-policy.yaml
kubectl delete -f ../network-policies/monitoring-policy.yaml
kubectl delete -f ../network-policies/logging-policy.yaml

# Delete resources in each namespace
delete_namespace_resources "app"
delete_namespace_resources "monitoring"
delete_namespace_resources "logging"

# Delete PVs (cluster-wide resource)
echo "Deleting Persistent Volumes..."
kubectl delete pv --all

# Delete cluster roles and bindings
echo "Deleting cluster roles and bindings..."
kubectl delete clusterrole filebeat
kubectl delete clusterrolebinding filebeat

# Delete any remaining resources
echo "Deleting any remaining resources..."
kubectl delete all --all -A

echo "Cleanup complete!"
echo "Note: Some resources may take a few minutes to be fully deleted."
echo "You can check the status with: kubectl get all -A" 