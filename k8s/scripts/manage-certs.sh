#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  generate  Generate a new SSL certificate"
    echo "  install   Install certificates to Kubernetes"
    echo "  renew     Renew existing certificates"
    echo "  list      List installed certificates"
    echo "  delete    Delete certificates"
    echo
    echo "Options:"
    echo "  -n, --namespace    Namespace (default: app)"
    echo "  -d, --domain       Domain name"
    echo "  -e, --email        Email address for Let's Encrypt"
    echo "  -s, --secret       Secret name for storing certificates"
    echo "  --staging          Use Let's Encrypt staging environment"
    echo
    echo "Examples:"
    echo "  $0 generate -d example.com -e admin@example.com"
    echo "  $0 install -d example.com -s tls-secret"
    echo "  $0 renew -s tls-secret"
    exit 1
}

# Function to validate domain name
validate_domain() {
    local domain=$1
    if [[ ! $domain =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
        echo "Error: Invalid domain name"
        exit 1
    fi
}

# Function to validate email
validate_email() {
    local email=$1
    if [[ ! $email =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        echo "Error: Invalid email address"
        exit 1
    fi
}

# Function to generate self-signed certificate
generate_self_signed() {
    local domain=$1
    local output_dir="certs/$domain"
    
    mkdir -p $output_dir
    
    # Generate private key
    openssl genrsa -out "$output_dir/tls.key" 2048
    
    # Generate CSR
    openssl req -new -key "$output_dir/tls.key" \
        -out "$output_dir/tls.csr" \
        -subj "/CN=$domain"
    
    # Generate certificate
    openssl x509 -req -days 365 \
        -in "$output_dir/tls.csr" \
        -signkey "$output_dir/tls.key" \
        -out "$output_dir/tls.crt"
    
    echo "Self-signed certificate generated in $output_dir"
}

# Function to generate Let's Encrypt certificate
generate_letsencrypt() {
    local domain=$1
    local email=$2
    local staging=$3
    local output_dir="certs/$domain"
    
    mkdir -p $output_dir
    
    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot..."
        pip install certbot
    fi
    
    # Generate certificate
    local staging_arg=""
    if [ "$staging" = true ]; then
        staging_arg="--staging"
    fi
    
    certbot certonly \
        --manual \
        --preferred-challenges=dns \
        --email $email \
        --agree-tos \
        --no-eff-email \
        $staging_arg \
        -d $domain
    
    # Copy certificates to output directory
    cp /etc/letsencrypt/live/$domain/fullchain.pem "$output_dir/tls.crt"
    cp /etc/letsencrypt/live/$domain/privkey.pem "$output_dir/tls.key"
    
    echo "Let's Encrypt certificate generated in $output_dir"
}

# Function to install certificates to Kubernetes
install_certs() {
    local domain=$1
    local secret_name=$2
    local namespace=${3:-app}
    local cert_dir="certs/$domain"
    
    if [ ! -d "$cert_dir" ]; then
        echo "Error: Certificate directory $cert_dir not found"
        exit 1
    fi
    
    if [ ! -f "$cert_dir/tls.crt" ] || [ ! -f "$cert_dir/tls.key" ]; then
        echo "Error: Certificate files not found in $cert_dir"
        exit 1
    fi
    
    # Create TLS secret
    kubectl create secret tls $secret_name \
        --cert="$cert_dir/tls.crt" \
        --key="$cert_dir/tls.key" \
        -n $namespace
    
    if [ $? -eq 0 ]; then
        echo "Certificates installed successfully"
        
        # Update ingress to use the new certificate
        kubectl patch ingress app-ingress -n $namespace -p "{
            \"spec\": {
                \"tls\": [{
                    \"hosts\": [\"$domain\"],
                    \"secretName\": \"$secret_name\"
                }]
            }
        }"
    else
        echo "Error: Failed to install certificates"
        exit 1
    fi
}

# Function to renew certificates
renew_certs() {
    local secret_name=$1
    local namespace=${2:-app}
    
    # Get domain from secret
    local domain=$(kubectl get secret $secret_name -n $namespace \
        -o jsonpath='{.metadata.annotations.cert-manager\.io/common-name}')
    
    if [ -z "$domain" ]; then
        echo "Error: Could not determine domain from secret"
        exit 1
    fi
    
    echo "Renewing certificate for $domain"
    certbot renew --cert-name $domain
    
    if [ $? -eq 0 ]; then
        # Update Kubernetes secret
        kubectl create secret tls $secret_name \
            --cert="/etc/letsencrypt/live/$domain/fullchain.pem" \
            --key="/etc/letsencrypt/live/$domain/privkey.pem" \
            -n $namespace \
            --dry-run=client -o yaml | \
        kubectl replace -f -
        
        echo "Certificate renewed successfully"
    else
        echo "Error: Failed to renew certificate"
        exit 1
    fi
}

# Function to list certificates
list_certs() {
    local namespace=${1:-app}
    
    echo "TLS secrets in namespace $namespace:"
    kubectl get secrets -n $namespace \
        -l "app.kubernetes.io/managed-by=cert-manager"
}

# Function to delete certificates
delete_certs() {
    local secret_name=$1
    local namespace=${2:-app}
    
    if ! kubectl get secret $secret_name -n $namespace &> /dev/null; then
        echo "Error: Secret $secret_name does not exist"
        exit 1
    fi
    
    read -p "Are you sure you want to delete certificate secret $secret_name? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete secret $secret_name -n $namespace
        if [ $? -eq 0 ]; then
            echo "Certificate secret deleted successfully"
        else
            echo "Error: Failed to delete certificate secret"
            exit 1
        fi
    else
        echo "Operation cancelled"
    fi
}

# Parse command line arguments
if [ $# -lt 1 ]; then
    usage
fi

command=$1
shift

namespace="app"
domain=""
email=""
secret_name=""
staging=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            namespace="$2"
            shift 2
            ;;
        -d|--domain)
            domain="$2"
            shift 2
            ;;
        -e|--email)
            email="$2"
            shift 2
            ;;
        -s|--secret)
            secret_name="$2"
            shift 2
            ;;
        --staging)
            staging=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

case $command in
    generate)
        if [ -z "$domain" ]; then
            echo "Error: Domain is required for generate command"
            usage
        fi
        
        validate_domain $domain
        
        if [ -z "$email" ]; then
            echo "Generating self-signed certificate"
            generate_self_signed $domain
        else
            validate_email $email
            echo "Generating Let's Encrypt certificate"
            generate_letsencrypt $domain $email $staging
        fi
        ;;
        
    install)
        if [ -z "$domain" ] || [ -z "$secret_name" ]; then
            echo "Error: Domain and secret name are required for install command"
            usage
        fi
        
        validate_domain $domain
        install_certs $domain $secret_name $namespace
        ;;
        
    renew)
        if [ -z "$secret_name" ]; then
            echo "Error: Secret name is required for renew command"
            usage
        fi
        
        renew_certs $secret_name $namespace
        ;;
        
    list)
        list_certs $namespace
        ;;
        
    delete)
        if [ -z "$secret_name" ]; then
            echo "Error: Secret name is required for delete command"
            usage
        fi
        
        delete_certs $secret_name $namespace
        ;;
        
    *)
        echo "Unknown command: $command"
        usage
        ;;
esac 