# Test and Schedule Setup Script
# Bu script servisi test eder ve Cloud Scheduler'ı kurar

$env:Path += ";C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin"
$PROJECT = "gen-lang-client-0307562385"
$REGION = "europe-west1"
$SERVICE_NAME = "mergenlite-backend"

Write-Host "========================================" -ForegroundColor Green
Write-Host "MergenLite Service Test & Schedule Setup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Step 1: Get Service URL
Write-Host "Step 1: Getting service URL..." -ForegroundColor Yellow
try {
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)" --project $PROJECT
    Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to get service URL: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Health Check
Write-Host "Step 2: Testing health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$SERVICE_URL/api/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response: $($response.Content)" -ForegroundColor White
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Health check PASSED!" -ForegroundColor Green
    } else {
        Write-Host "⚠ Health check returned non-200 status" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Health check FAILED: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Checking logs..." -ForegroundColor Yellow
    Write-Host "Log URL: https://console.cloud.google.com/logs/viewer?project=$PROJECT" -ForegroundColor Cyan
}

Write-Host ""

# Step 3: Create Cloud Scheduler Job
Write-Host "Step 3: Creating Cloud Scheduler job..." -ForegroundColor Yellow
try {
    # Check if job already exists
    $existingJob = gcloud scheduler jobs describe daily-hotel-scan --location $REGION --project $PROJECT 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Job already exists. Updating..." -ForegroundColor Yellow
        gcloud scheduler jobs update http daily-hotel-scan `
            --schedule "0 7 * * *" `
            --uri "$SERVICE_URL/api/jobs/daily-scan" `
            --http-method POST `
            --headers "Content-Type=application/json" `
            --message-body '{\"target_id\": \"721110\", \"naics_code\": \"721110\", \"days_back\": 1, \"limit\": 10, \"force_refresh\": false}' `
            --time-zone "Europe/Istanbul" `
            --location $REGION `
            --project $PROJECT
        Write-Host "✓ Job updated successfully!" -ForegroundColor Green
    } else {
        Write-Host "Creating new job..." -ForegroundColor Yellow
        gcloud scheduler jobs create http daily-hotel-scan `
            --schedule "0 7 * * *" `
            --uri "$SERVICE_URL/api/jobs/daily-scan" `
            --http-method POST `
            --headers "Content-Type=application/json" `
            --message-body '{\"target_id\": \"721110\", \"naics_code\": \"721110\", \"days_back\": 1, \"limit\": 10, \"force_refresh\": false}' `
            --time-zone "Europe/Istanbul" `
            --location $REGION `
            --project $PROJECT
        Write-Host "✓ Job created successfully!" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Failed to create/update scheduler job: $_" -ForegroundColor Red
}

Write-Host ""

# Step 4: Manual Trigger (Optional)
Write-Host "Step 4: Manual trigger (optional)..." -ForegroundColor Yellow
$trigger = Read-Host "Manuel test yapmak ister misiniz? (y/n)"
if ($trigger -eq "y" -or $trigger -eq "Y") {
    try {
        Write-Host "Triggering job manually..." -ForegroundColor Yellow
        gcloud scheduler jobs run daily-hotel-scan --location $REGION --project $PROJECT
        Write-Host "✓ Job triggered! Check your email in a few minutes." -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to trigger job: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "Scheduler: daily-hotel-scan (runs daily at 07:00 Istanbul time)" -ForegroundColor Cyan
Write-Host ""

