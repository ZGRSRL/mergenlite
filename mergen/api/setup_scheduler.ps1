# Cloud Scheduler Setup Script
# Usage: .\mergen\api\setup_scheduler.ps1

$env:Path += ";C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Cloud Scheduler Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get service URL
Write-Host "1. Getting service URL..." -ForegroundColor Yellow
$SERVICE_URL = gcloud run services describe mergenlite-backend --region europe-west1 --format "value(status.url)" 2>&1

if ($SERVICE_URL -and $SERVICE_URL -notmatch "ERROR") {
    Write-Host "   Service URL: $SERVICE_URL" -ForegroundColor Green
    Write-Host ""
    
    # Check if job already exists
    Write-Host "2. Checking if scheduler job exists..." -ForegroundColor Yellow
    $existingJob = gcloud scheduler jobs describe daily-hotel-scan --location europe-west1 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Job already exists, updating..." -ForegroundColor Yellow
        gcloud scheduler jobs update http daily-hotel-scan `
          --schedule "0 7 * * *" `
          --uri "$SERVICE_URL/api/jobs/daily-scan" `
          --http-method POST `
          --headers "Content-Type=application/json" `
          --message-body '{"target_id": "721110", "naics_code": "721110", "days_back": 1, "limit": 10, "force_refresh": false}' `
          --time-zone "Europe/Istanbul" `
          --location europe-west1
    } else {
        Write-Host "   Creating new scheduler job..." -ForegroundColor Yellow
        gcloud scheduler jobs create http daily-hotel-scan `
          --schedule "0 7 * * *" `
          --uri "$SERVICE_URL/api/jobs/daily-scan" `
          --http-method POST `
          --headers "Content-Type=application/json" `
          --message-body '{"target_id": "721110", "naics_code": "721110", "days_back": 1, "limit": 10, "force_refresh": false}' `
          --time-zone "Europe/Istanbul" `
          --location europe-west1
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "SUCCESS: Cloud Scheduler job created/updated!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Test the job manually:" -ForegroundColor White
        Write-Host "   gcloud scheduler jobs run daily-hotel-scan --location europe-west1" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "2. Check job status:" -ForegroundColor White
        Write-Host "   gcloud scheduler jobs describe daily-hotel-scan --location europe-west1" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "3. View job execution history:" -ForegroundColor White
        Write-Host "   gcloud scheduler jobs list --location europe-west1" -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Failed to create/update scheduler job" -ForegroundColor Red
    }
} else {
    Write-Host "ERROR: Could not get service URL" -ForegroundColor Red
    Write-Host "Make sure the service is deployed successfully" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
