# Cloud Run Final Deployment Script (PowerShell)
# Bu script Cloud SQL ile çalışan final deployment için hazırlanmıştır

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$true)]
    [string]$CloudSqlInstance,  # Format: project-id:region:instance-name
    
    [string]$Region = "europe-west1",
    [string]$ServiceName = "mergenlite-backend",
    [string]$SourceDir = "./mergen/api"
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "MergenLite Cloud Run Final Deployment" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Validate Cloud SQL instance format
if ($CloudSqlInstance -notmatch '^[^:]+:[^:]+:[^:]+$') {
    Write-Host "ERROR: Cloud SQL instance format should be: project-id:region:instance-name" -ForegroundColor Red
    Write-Host "Example: my-project:europe-west1:mergenlite-db" -ForegroundColor Yellow
    exit 1
}

# Set project
Write-Host "Setting GCP project to: $ProjectId" -ForegroundColor Yellow
gcloud config set project $ProjectId

# Read environment variables
Write-Host ""
Write-Host "Required Environment Variables:" -ForegroundColor Yellow
$OpenAIApiKey = Read-Host "Enter OPENAI_API_KEY"
$AmadeusApiKey = Read-Host "Enter AMADEUS_API_KEY"
$AmadeusApiSecret = Read-Host "Enter AMADEUS_API_SECRET" -AsSecureString
$AmadeusApiSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($AmadeusApiSecret))

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
$SmtpUsername = ""
$SmtpPasswordPlain = ""
$NotificationEmail = ""

if (-not [string]::IsNullOrEmpty($SmtpHost)) {
    $SmtpUsername = Read-Host "Enter SMTP_USERNAME"
    $SmtpPassword = Read-Host "Enter SMTP_PASSWORD" -AsSecureString
    $SmtpPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SmtpPassword))
    $NotificationEmail = Read-Host "Enter PIPELINE_NOTIFICATION_EMAIL"
}

# Build environment variables
# Cloud SQL uses Unix socket: /cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
# But for connection string, we use the instance connection name directly
$PostgresHost = $CloudSqlInstance  # Cloud SQL connection name

$EnvVars = "OPENAI_API_KEY=$OpenAIApiKey"
$EnvVars += ",AMADEUS_API_KEY=$AmadeusApiKey"
$EnvVars += ",AMADEUS_API_SECRET=$AmadeusApiSecretPlain"
$EnvVars += ",POSTGRES_HOST=$PostgresHost"
$EnvVars += ",POSTGRES_USER=$PostgresUser"
$EnvVars += ",POSTGRES_PASSWORD=$PostgresPasswordPlain"
$EnvVars += ",POSTGRES_DB=$PostgresDb"
$EnvVars += ",POSTGRES_PORT=$PostgresPort"
$EnvVars += ",AMADEUS_ENV=production"
$EnvVars += ",PORT=8080"

if (-not [string]::IsNullOrEmpty($SmtpHost)) {
    $EnvVars += ",SMTP_HOST=$SmtpHost"
    $EnvVars += ",SMTP_USERNAME=$SmtpUsername"
    $EnvVars += ",SMTP_PASSWORD=$SmtpPasswordPlain"
    $EnvVars += ",SMTP_PORT=587"
    $EnvVars += ",SMTP_USE_TLS=true"
    if (-not [string]::IsNullOrEmpty($NotificationEmail)) {
        $EnvVars += ",PIPELINE_NOTIFICATION_EMAIL=$NotificationEmail"
    }
}

Write-Host ""
Write-Host "Deploying to Cloud Run..." -ForegroundColor Green
Write-Host "Cloud SQL Instance: $CloudSqlInstance" -ForegroundColor Cyan
Write-Host ""

# Deploy to Cloud Run
gcloud run deploy $ServiceName `
  --source $SourceDir `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --port 8080 `
  --memory 2Gi `
  --cpu 2 `
  --timeout 3600 `
  --max-instances 10 `
  --add-cloudsql-instances $CloudSqlInstance `
  --set-env-vars $EnvVars

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URL:" -ForegroundColor Cyan
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format="value(status.url)"
Write-Host $ServiceUrl -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Test the service: curl $ServiceUrl/api/health" -ForegroundColor White
Write-Host "2. Set up Cloud Scheduler (see CLOUD_SCHEDULER_SETUP.md)" -ForegroundColor White
Write-Host ""

