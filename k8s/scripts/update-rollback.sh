#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [update|rollback] [service] [options]"
    echo
    echo "Commands:"
    echo "  update   Update a service to a new version"
    echo "  rollback Roll back a service to a previous version"
    echo
    echo "Services:"
    echo "  frontend       Frontend service"
    echo "  flask-backend  Flask backend service"
    echo "  node-backend   Node.js backend service"
    echo
    echo "Options:"
    echo "  -i, --image   New image for update (required for update)"
    echo "  -r, --revision Revision to rollback to (required for rollback)"
    echo
    echo "Examples:"
    echo "  $0 update frontend -i myregistry/frontend:v2"
    echo "  $0 rollback flask-backend -r 1"
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

# Function to update a deployment
update_deployment() {
    local deployment=$1
    local image=$2
    
    echo "Updating deployment $deployment with image $image"
    kubectl set image deployment/$deployment $deployment=$image
    
    echo "Waiting for rollout to complete..."
    if ! kubectl rollout status deployment/$deployment --timeout=300s; then
        echo "Rollout failed! Rolling back..."
        kubectl rollout undo deployment/$deployment
        exit 1
    fi
    
    echo "Update successful!"
}

# Function to rollback a deployment
rollback_deployment() {
    local deployment=$1
    local revision=$2
    
    echo "Rolling back deployment $deployment to revision $revision"
    kubectl rollout undo deployment/$deployment --to-revision=$revision
    
    echo "Waiting for rollback to complete..."
    if ! kubectl rollout status deployment/$deployment --timeout=300s; then
        echo "Rollback failed!"
        exit 1
    fi
    
    echo "Rollback successful!"
}

# Parse command line arguments
if [ $# -lt 2 ]; then
    usage
fi

command=$1
service=$2
shift 2

case $command in
    update)
        while [[ $# -gt 0 ]]; do
            case $1 in
                -i|--image)
                    image="$2"
                    shift 2
                    ;;
                *)
                    echo "Unknown option: $1"
                    usage
                    ;;
            esac
        done
        
        if [ -z "$image" ]; then
            echo "Error: Image is required for update"
            usage
        fi
        
        check_deployment $service
        update_deployment $service $image
        ;;
        
    rollback)
        while [[ $# -gt 0 ]]; do
            case $1 in
                -r|--revision)
                    revision="$2"
                    shift 2
                    ;;
                *)
                    echo "Unknown option: $1"
                    usage
                    ;;
            esac
        done
        
        if [ -z "$revision" ]; then
            echo "Error: Revision is required for rollback"
            usage
        fi
        
        check_deployment $service
        rollback_deployment $service $revision
        ;;
        
    *)
        echo "Unknown command: $command"
        usage
        ;;
esac

# Display deployment status
echo
echo "Current deployment status:"
kubectl get deployment $service
echo
echo "Deployment history:"
kubectl rollout history deployment/$service 