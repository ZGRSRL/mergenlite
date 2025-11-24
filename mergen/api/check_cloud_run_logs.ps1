# Cloud Run Logs Checker Script
# Usage: .\check_cloud_run_logs.ps1

param(
    [string]$ServiceName = "mergenlite-backend",
    [string]$Region = "europe-west1",
    [int]$Limit = 50
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "Cloud Run Logs Checker" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: gcloud CLI is not installed" -ForegroundColor Red
    Write-Host "Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

Write-Host "Fetching logs for service: $ServiceName" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host "Limit: $Limit" -ForegroundColor Cyan
Write-Host ""

# Get logs
Write-Host "Recent logs:" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray
gcloud run services logs read $ServiceName --region $Region --limit $Limit

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Log Analysis Tips:" -ForegroundColor Yellow
Write-Host "1. Look for 'ModuleNotFoundError' - missing Python package" -ForegroundColor White
Write-Host "2. Look for 'OperationalError' - database connection issue" -ForegroundColor White
Write-Host "3. Look for 'SyntaxError' - code syntax error" -ForegroundColor White
Write-Host "4. Look for 'ImportError' - import path issue" -ForegroundColor White
Write-Host "5. Look for 'Connection refused' - port/database issue" -ForegroundColor White
Write-Host ""

