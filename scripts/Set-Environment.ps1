param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('development','test','production')]
    [string]$Environment
)

Write-Host "Setting up $Environment environment..."

# Copy appropriate env file
Copy-Item "./config/.env.$Environment" ".env"

# If production environment, load secrets
if ($Environment -eq "production") {
    $secretsPath = "./config/secrets.production"
    if (Test-Path $secretsPath) {
        Write-Host "Loading production secrets..."
        
        # Read secrets file
        $secrets = Get-Content $secretsPath | ConvertFrom-StringData
        
        # Read .env file
        $envContent = Get-Content ".env"
        
        # Replace placeholders with actual values
        $envContent = $envContent -replace '\${PROD_DB_USER}', $secrets.PROD_DB_USER
        $envContent = $envContent -replace '\${PROD_DB_PASSWORD}', $secrets.PROD_DB_PASSWORD
        $envContent = $envContent -replace '\${PROD_JWT_SECRET}', $secrets.PROD_JWT_SECRET
        $envContent = $envContent -replace '\${PROD_REDIS_PASSWORD}', $secrets.PROD_REDIS_PASSWORD
        $envContent = $envContent -replace '\${PROD_GRAFANA_PASSWORD}', $secrets.PROD_GRAFANA_PASSWORD
        
        # Write updated content back to .env
        $envContent | Set-Content ".env"
    }
    else {
        Write-Error "Production secrets file not found. Run Generate-Secrets.ps1 first."
        exit 1
    }
}

# Apply Kubernetes configurations if they exist
$k8sConfigPath = "k8s/config/$Environment"
if (Test-Path $k8sConfigPath) {
    Write-Host "Applying Kubernetes configurations for $Environment environment..."
    kubectl apply -f $k8sConfigPath
}

Write-Host "Environment set to $Environment"
Write-Host "Configuration loaded from ./config/.env.$Environment" 