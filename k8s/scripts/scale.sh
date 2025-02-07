#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [manual|auto] [service] [options]"
    echo
    echo "Commands:"
    echo "  manual  Manually scale a deployment"
    echo "  auto    Configure autoscaling for a deployment"
    echo
    echo "Services:"
    echo "  frontend       Frontend service"
    echo "  flask-backend  Flask backend service"
    echo "  node-backend   Node.js backend service"
    echo
    echo "Options for manual scaling:"
    echo "  -r, --replicas  Number of replicas (required)"
    echo
    echo "Options for autoscaling:"
    echo "  --min          Minimum number of replicas (required)"
    echo "  --max          Maximum number of replicas (required)"
    echo "  --cpu          Target CPU utilization percentage (default: 70)"
    echo "  --memory       Target memory utilization percentage (default: 80)"
    echo
    echo "Examples:"
    echo "  $0 manual frontend -r 3"
    echo "  $0 auto flask-backend --min 2 --max 5 --cpu 75 --memory 85"
    exit 1
}

# Function to check if a deployment exists
check_deployment() {
    local deployment=$1
    if ! kubectl get deployment $deployment &> /dev/null; then
        echo "Error: Deployment $deployment not found"
        exit 1
    fi
}

# Function to manually scale a deployment
scale_deployment() {
    local deployment=$1
    local replicas=$2
    
    echo "Scaling deployment $deployment to $replicas replicas"
    kubectl scale deployment/$deployment --replicas=$replicas
    
    echo "Waiting for scaling to complete..."
    kubectl rollout status deployment/$deployment --timeout=300s
    
    echo "Current deployment status:"
    kubectl get deployment $deployment
}

# Function to configure autoscaling
configure_autoscaling() {
    local deployment=$1
    local min_replicas=$2
    local max_replicas=$3
    local cpu_target=${4:-70}
    local memory_target=${5:-80}
    
    echo "Configuring autoscaling for deployment $deployment"
    echo "Min replicas: $min_replicas"
    echo "Max replicas: $max_replicas"
    echo "CPU target: $cpu_target%"
    echo "Memory target: $memory_target%"
    
    # Delete existing HPA if it exists
    kubectl delete hpa $deployment 2>/dev/null || true
    
    # Create new HPA
    kubectl autoscale deployment $deployment \
        --min=$min_replicas \
        --max=$max_replicas \
        --cpu-percent=$cpu_target
    
    # Add memory target using patch
    kubectl patch hpa $deployment --patch "{
        \"spec\": {
            \"metrics\": [
                {
                    \"type\": \"Resource\",
                    \"resource\": {
                        \"name\": \"memory\",
                        \"target\": {
                            \"type\": \"Utilization\",
                            \"averageUtilization\": $memory_target
                        }
                    }
                }
            ]
        }
    }"
    
    echo "Autoscaling configuration complete"
    echo
    echo "Current HPA status:"
    kubectl get hpa $deployment
}

# Parse command line arguments
if [ $# -lt 2 ]; then
    usage
fi

command=$1
service=$2
shift 2

case $command in
    manual)
        while [[ $# -gt 0 ]]; do
            case $1 in
                -r|--replicas)
                    replicas="$2"
                    shift 2
                    ;;
                *)
                    echo "Unknown option: $1"
                    usage
                    ;;
            esac
        done
        
        if [ -z "$replicas" ]; then
            echo "Error: Number of replicas is required for manual scaling"
            usage
        fi
        
        check_deployment $service
        scale_deployment $service $replicas
        ;;
        
    auto)
        while [[ $# -gt 0 ]]; do
            case $1 in
                --min)
                    min_replicas="$2"
                    shift 2
                    ;;
                --max)
                    max_replicas="$2"
                    shift 2
                    ;;
                --cpu)
                    cpu_target="$2"
                    shift 2
                    ;;
                --memory)
                    memory_target="$2"
                    shift 2
                    ;;
                *)
                    echo "Unknown option: $1"
                    usage
                    ;;
            esac
        done
        
        if [ -z "$min_replicas" ] || [ -z "$max_replicas" ]; then
            echo "Error: Both minimum and maximum replicas are required for autoscaling"
            usage
        fi
        
        check_deployment $service
        configure_autoscaling $service $min_replicas $max_replicas $cpu_target $memory_target
        ;;
        
    *)
        echo "Unknown command: $command"
        usage
        ;;
esac 