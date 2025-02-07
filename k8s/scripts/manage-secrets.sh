#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  create    Create a new secret"
    echo "  update    Update an existing secret"
    echo "  delete    Delete a secret"
    echo "  view      View secret details"
    echo "  list      List all secrets"
    echo "  rotate    Rotate secret values"
    echo
    echo "Options:"
    echo "  -n, --namespace  Namespace (default: app)"
    echo "  -s, --secret     Secret name"
    echo "  -k, --key        Key name for create/update"
    echo "  -v, --value      Value for create/update"
    echo "  -f, --file       File containing key-value pairs"
    echo
    echo "Examples:"
    echo "  $0 create -s my-secret -k api-key -v 12345"
    echo "  $0 update -s my-secret -f secrets.env"
    echo "  $0 view -s my-secret"
    echo "  $0 rotate -s postgres-secret"
    exit 1
}

# Function to validate input
validate_input() {
    local secret_name=$1
    if [[ ! $secret_name =~ ^[a-z0-9][a-z0-9-]*[a-z0-9]$ ]]; then
        echo "Error: Invalid secret name. Must consist of lowercase alphanumeric characters or '-'"
        exit 1
    fi
}

# Function to create secret
create_secret() {
    local secret_name=$1
    local key=$2
    local value=$3
    local namespace=${4:-app}
    
    validate_input $secret_name
    
    if kubectl get secret $secret_name -n $namespace &> /dev/null; then
        echo "Error: Secret $secret_name already exists"
        exit 1
    fi
    
    echo "Creating secret $secret_name"
    kubectl create secret generic $secret_name \
        --from-literal=$key=$value \
        -n $namespace
    
    if [ $? -eq 0 ]; then
        echo "Secret created successfully"
    else
        echo "Error: Failed to create secret"
        exit 1
    fi
}

# Function to update secret
update_secret() {
    local secret_name=$1
    local namespace=${2:-app}
    local file=$3
    
    validate_input $secret_name
    
    if [ ! -f "$file" ]; then
        echo "Error: File $file not found"
        exit 1
    fi
    
    if ! kubectl get secret $secret_name -n $namespace &> /dev/null; then
        echo "Error: Secret $secret_name does not exist"
        exit 1
    fi
    
    echo "Updating secret $secret_name"
    kubectl create secret generic $secret_name \
        --from-env-file=$file \
        -n $namespace \
        -o yaml \
        --dry-run=client | \
    kubectl replace -f -
    
    if [ $? -eq 0 ]; then
        echo "Secret updated successfully"
    else
        echo "Error: Failed to update secret"
        exit 1
    fi
}

# Function to delete secret
delete_secret() {
    local secret_name=$1
    local namespace=${2:-app}
    
    validate_input $secret_name
    
    if ! kubectl get secret $secret_name -n $namespace &> /dev/null; then
        echo "Error: Secret $secret_name does not exist"
        exit 1
    fi
    
    read -p "Are you sure you want to delete secret $secret_name? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete secret $secret_name -n $namespace
        if [ $? -eq 0 ]; then
            echo "Secret deleted successfully"
        else
            echo "Error: Failed to delete secret"
            exit 1
        fi
    else
        echo "Operation cancelled"
    fi
}

# Function to view secret
view_secret() {
    local secret_name=$1
    local namespace=${2:-app}
    
    validate_input $secret_name
    
    if ! kubectl get secret $secret_name -n $namespace &> /dev/null; then
        echo "Error: Secret $secret_name does not exist"
        exit 1
    fi
    
    echo "Secret details:"
    kubectl get secret $secret_name -n $namespace -o yaml
    
    echo
    echo "Decoded values:"
    kubectl get secret $secret_name -n $namespace -o json | \
        jq -r '.data | map_values(@base64d)'
}

# Function to list secrets
list_secrets() {
    local namespace=${1:-app}
    
    echo "Secrets in namespace $namespace:"
    kubectl get secrets -n $namespace
}

# Function to rotate secret values
rotate_secrets() {
    local secret_name=$1
    local namespace=${2:-app}
    
    validate_input $secret_name
    
    if ! kubectl get secret $secret_name -n $namespace &> /dev/null; then
        echo "Error: Secret $secret_name does not exist"
        exit 1
    fi
    
    case $secret_name in
        postgres-secret)
            # Generate new PostgreSQL password
            local new_password=$(openssl rand -base64 32)
            
            echo "Rotating PostgreSQL credentials"
            kubectl create secret generic $secret_name \
                --from-literal=POSTGRES_PASSWORD=$new_password \
                --from-literal=POSTGRES_USER=postgres \
                -n $namespace \
                -o yaml \
                --dry-run=client | \
            kubectl replace -f -
            
            # Update applications that use the database
            kubectl rollout restart deployment/flask-backend -n $namespace
            kubectl rollout restart deployment/node-backend -n $namespace
            ;;
            
        *)
            echo "Error: Rotation not implemented for secret $secret_name"
            exit 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        echo "Secret rotation completed successfully"
    else
        echo "Error: Failed to rotate secret"
        exit 1
    fi
}

# Parse command line arguments
if [ $# -lt 1 ]; then
    usage
fi

command=$1
shift

namespace="app"
secret_name=""
key=""
value=""
file=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            namespace="$2"
            shift 2
            ;;
        -s|--secret)
            secret_name="$2"
            shift 2
            ;;
        -k|--key)
            key="$2"
            shift 2
            ;;
        -v|--value)
            value="$2"
            shift 2
            ;;
        -f|--file)
            file="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

case $command in
    create)
        if [ -z "$secret_name" ] || [ -z "$key" ] || [ -z "$value" ]; then
            echo "Error: Secret name, key, and value are required for create command"
            usage
        fi
        create_secret $secret_name $key $value $namespace
        ;;
    update)
        if [ -z "$secret_name" ] || [ -z "$file" ]; then
            echo "Error: Secret name and file are required for update command"
            usage
        fi
        update_secret $secret_name $namespace $file
        ;;
    delete)
        if [ -z "$secret_name" ]; then
            echo "Error: Secret name is required for delete command"
            usage
        fi
        delete_secret $secret_name $namespace
        ;;
    view)
        if [ -z "$secret_name" ]; then
            echo "Error: Secret name is required for view command"
            usage
        fi
        view_secret $secret_name $namespace
        ;;
    list)
        list_secrets $namespace
        ;;
    rotate)
        if [ -z "$secret_name" ]; then
            echo "Error: Secret name is required for rotate command"
            usage
        fi
        rotate_secrets $secret_name $namespace
        ;;
    *)
        echo "Unknown command: $command"
        usage
        ;;
esac 