#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [command] [service] [options]"
    echo
    echo "Commands:"
    echo "  logs       View logs for a service"
    echo "  describe   Describe a resource"
    echo "  events     View events"
    echo "  metrics    View metrics"
    echo "  status     View status of all resources"
    echo "  port-forward  Forward ports for a service"
    echo
    echo "Services:"
    echo "  frontend       Frontend service"
    echo "  flask-backend  Flask backend service"
    echo "  node-backend   Node.js backend service"
    echo "  postgres      PostgreSQL database"
    echo "  grafana       Grafana monitoring"
    echo "  prometheus    Prometheus monitoring"
    echo "  kibana        Kibana logging"
    echo
    echo "Options:"
    echo "  -n, --namespace  Namespace (default: app)"
    echo "  -f, --follow     Follow logs"
    echo "  -t, --tail       Number of lines to show (default: 100)"
    echo "  -p, --port       Port to forward to (required for port-forward)"
    echo
    echo "Examples:"
    echo "  $0 logs frontend -f"
    echo "  $0 describe pod flask-backend"
    echo "  $0 metrics node-backend"
    echo "  $0 port-forward grafana -p 3000"
    exit 1
}

# Function to get pod name
get_pod_name() {
    local service=$1
    local namespace=${2:-app}
    kubectl get pods -n $namespace -l app=$service -o jsonpath="{.items[0].metadata.name}"
}

# Function to view logs
view_logs() {
    local service=$1
    local namespace=${2:-app}
    local follow=$3
    local tail=${4:-100}
    
    local pod=$(get_pod_name $service $namespace)
    if [ -z "$pod" ]; then
        echo "Error: No pods found for service $service in namespace $namespace"
        exit 1
    fi
    
    if [ "$follow" = true ]; then
        kubectl logs -f -n $namespace $pod --tail=$tail
    else
        kubectl logs -n $namespace $pod --tail=$tail
    fi
}

# Function to describe resource
describe_resource() {
    local resource_type=$1
    local resource_name=$2
    local namespace=${3:-app}
    
    kubectl describe $resource_type $resource_name -n $namespace
}

# Function to view events
view_events() {
    local namespace=${1:-app}
    
    kubectl get events -n $namespace --sort-by='.lastTimestamp'
}

# Function to view metrics
view_metrics() {
    local service=$1
    local namespace=${2:-app}
    
    local pod=$(get_pod_name $service $namespace)
    if [ -z "$pod" ]; then
        echo "Error: No pods found for service $service in namespace $namespace"
        exit 1
    fi
    
    echo "Pod Metrics:"
    kubectl top pod $pod -n $namespace
    
    echo
    echo "Node Metrics:"
    kubectl top node
}

# Function to view status
view_status() {
    local namespace=${1:-app}
    
    echo "Deployments:"
    kubectl get deployments -n $namespace
    
    echo
    echo "Pods:"
    kubectl get pods -n $namespace
    
    echo
    echo "Services:"
    kubectl get services -n $namespace
    
    echo
    echo "HPAs:"
    kubectl get hpa -n $namespace
    
    echo
    echo "Network Policies:"
    kubectl get networkpolicies -n $namespace
}

# Function to port forward
port_forward() {
    local service=$1
    local port=$2
    local namespace=${3:-app}
    
    echo "Port forwarding service $service to localhost:$port"
    kubectl port-forward -n $namespace svc/$service $port:$port
}

# Parse command line arguments
if [ $# -lt 2 ]; then
    usage
fi

command=$1
service=$2
shift 2

namespace="app"
follow=false
tail=100
port=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            namespace="$2"
            shift 2
            ;;
        -f|--follow)
            follow=true
            shift
            ;;
        -t|--tail)
            tail="$2"
            shift 2
            ;;
        -p|--port)
            port="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

case $command in
    logs)
        view_logs $service $namespace $follow $tail
        ;;
    describe)
        describe_resource pod $service $namespace
        ;;
    events)
        view_events $namespace
        ;;
    metrics)
        view_metrics $service $namespace
        ;;
    status)
        view_status $namespace
        ;;
    port-forward)
        if [ -z "$port" ]; then
            echo "Error: Port is required for port-forward command"
            usage
        fi
        port_forward $service $port $namespace
        ;;
    *)
        echo "Unknown command: $command"
        usage
        ;;
esac 