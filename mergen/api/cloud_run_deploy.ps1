# Cloud Run Deployment Script for MergenLite Backend (PowerShell)
# Usage: .\cloud_run_deploy.ps1

param(
    [string]$ProjectId = "",
    [string]$Region = "europe-west1",
    [string]$ServiceName = "mergenlite-backend",
    [string]$SourceDir = "./mergen/api"
)

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Green "========================================"
Write-ColorOutput Green "MergenLite Cloud Run Deployment"
Write-ColorOutput Green "========================================"
Write-Output ""

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "ERROR: gcloud CLI is not installed"
    Write-Output "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Get project ID if not provided
if ([string]::IsNullOrEmpty($ProjectId)) {
    $ProjectId = Read-Host "Enter GCP Project ID"
}

# Set project
Write-ColorOutput Yellow "Setting GCP project to: $ProjectId"
gcloud config set project $ProjectId

Write-Output ""
Write-ColorOutput Yellow "Required Environment Variables:"
Write-Output "  - OPENAI_API_KEY (required for LLM)"
Write-Output "  - AMADEUS_API_KEY (required for hotel search)"
Write-Output "  - AMADEUS_API_SECRET (required for hotel search)"
Write-Output "  - POSTGRES_HOST (Cloud SQL instance connection name)"
Write-Output "  - POSTGRES_USER (database user)"
Write-Output "  - POSTGRES_PASSWORD (database password)"
Write-Output "  - POSTGRES_DB (database name)"
Write-Output "  - SMTP_HOST (optional, for email notifications)"
Write-Output ""

# Read environment variables
$OpenAIApiKey = Read-Host "Enter OPENAI_API_KEY"
$AmadeusApiKey = Read-Host "Enter AMADEUS_API_KEY"
$AmadeusApiSecret = Read-Host "Enter AMADEUS_API_SECRET" -AsSecureString
$AmadeusApiSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($AmadeusApiSecret))

$PostgresHost = Read-Host "Enter POSTGRES_HOST (Cloud SQL connection name, e.g., project:region:instance)"
$PostgresUser = Read-Host "Enter POSTGRES_USER [postgres]"
if ([string]::IsNullOrEmpty($PostgresUser)) { $PostgresUser = "postgres" }

$PostgresPassword = Read-Host "Enter POSTGRES_PASSWORD" -AsSecureString
$PostgresPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($PostgresPassword))

$PostgresDb = Read-Host "Enter POSTGRES_DB [ZGR_AI]"
if ([string]::IsNullOrEmpty($PostgresDb)) { $PostgresDb = "ZGR_AI" }

$PostgresPort = Read-Host "Enter POSTGRES_PORT [5432]"
if ([string]::IsNullOrEmpty($PostgresPort)) { $PostgresPort = "5432" }

# Optional SMTP
$SmtpHost = Read-Host "Enter SMTP_HOST (optional, press Enter to skip)"
$EnvVars = "OPENAI_API_KEY=$OpenAIApiKey,AMADEUS_API_KEY=$AmadeusApiKey,AMADEUS_API_SECRET=$AmadeusApiSecretPlain,POSTGRES_HOST=$PostgresHost,POSTGRES_USER=$PostgresUser,POSTGRES_PASSWORD=$PostgresPasswordPlain,POSTGRES_DB=$PostgresDb,POSTGRES_PORT=$PostgresPort,AMADEUS_ENV=production,PORT=8080"

if (-not [string]::IsNullOrEmpty($SmtpHost)) {
    $SmtpUsername = Read-Host "Enter SMTP_USERNAME"
    $SmtpPassword = Read-Host "Enter SMTP_PASSWORD" -AsSecureString
    $SmtpPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SmtpPassword))
    $NotificationEmail = Read-Host "Enter PIPELINE_NOTIFICATION_EMAIL"
    
    $EnvVars += ",SMTP_HOST=$SmtpHost,SMTP_USERNAME=$SmtpUsername,SMTP_PASSWORD=$SmtpPasswordPlain,SMTP_PORT=587,SMTP_USE_TLS=true,PIPELINE_NOTIFICATION_EMAIL=$NotificationEmail"
}

Write-Output ""
Write-ColorOutput Green "Deploying to Cloud Run..."
Write-Output ""

# Deploy to Cloud Run
gcloud run deploy $ServiceName `
  --source $SourceDir `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --port 8080 `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars $EnvVars

Write-Output ""
Write-ColorOutput Green "========================================"
Write-ColorOutput Green "Deployment Complete!"
Write-ColorOutput Green "========================================"
Write-Output ""
Write-Output "Service URL:"
gcloud run services describe $ServiceName --region $Region --format="value(status.url)"
Write-Output ""

