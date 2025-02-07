param(
    [string]$DbUser = "dev_user",
    [string]$DbPassword = "dev-password-123",
    [string]$JwtSecret = "dev-jwt-secret-123",
    [string]$RedisPassword = "dev-redis-123",
    [string]$GrafanaPassword = "dev-grafana-123"
)

# Function to generate secure random string if needed
function Generate-Secret {
    $random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $bytes = New-Object byte[] 32
    $random.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

# Use provided values
$PROD_DB_USER = $DbUser
$PROD_DB_PASSWORD = $DbPassword
$PROD_JWT_SECRET = $JwtSecret
$PROD_REDIS_PASSWORD = $RedisPassword
$PROD_GRAFANA_PASSWORD = $GrafanaPassword

# Create config directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "./config" | Out-Null

# Create secrets file
@"
PROD_DB_USER=$PROD_DB_USER
PROD_DB_PASSWORD=$PROD_DB_PASSWORD
PROD_JWT_SECRET=$PROD_JWT_SECRET
PROD_REDIS_PASSWORD=$PROD_REDIS_PASSWORD
PROD_GRAFANA_PASSWORD=$PROD_GRAFANA_PASSWORD
"@ | Out-File -FilePath "./config/secrets.production" -Encoding UTF8

# Set appropriate permissions
$acl = Get-Acl "./config/secrets.production"
$acl.SetAccessRuleProtection($true, $false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($env:USERNAME, "Read,Write", "Allow")
$acl.AddAccessRule($rule)
Set-Acl "./config/secrets.production" $acl

Write-Host "Production secrets saved to ./config/secrets.production"
Write-Host "IMPORTANT: Store these secrets securely and never commit them to version control!"
Write-Host "Make sure to securely transfer these secrets to your production environment."

# Display usage instructions
Write-Host "`nUsage examples:"
Write-Host "1. Use default (development) values:"
Write-Host "   .\Generate-Secrets.ps1"
Write-Host "2. Use your own secrets:"
Write-Host "   .\Generate-Secrets.ps1 -DbUser 'myuser' -DbPassword 'mypass' -JwtSecret 'myjwt' -RedisPassword 'myredis' -GrafanaPassword 'mygrafana'" 