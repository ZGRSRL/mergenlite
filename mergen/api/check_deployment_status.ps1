# Cloud Run Deployment Status Checker
# Usage: .\mergen\api\check_deployment_status.ps1

$env:Path += ";C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Cloud Run Deployment Status" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$SERVICE_NAME = "mergenlite-backend"
$REGION = "europe-west1"
$PROJECT = "gen-lang-client-0307562385"

# Check if service exists
Write-Host "1. Checking service status..." -ForegroundColor Yellow
$service = gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT --format json 2>$null | ConvertFrom-Json

if ($service) {
    Write-Host "   Service exists: $($service.metadata.name)" -ForegroundColor Green
    Write-Host "   Status: $($service.status.conditions[0].status)" -ForegroundColor Cyan
    Write-Host "   URL: $($service.status.url)" -ForegroundColor Cyan
    Write-Host ""
    
    # Get latest revision
    Write-Host "2. Latest revision:" -ForegroundColor Yellow
    $revisions = gcloud run revisions list --service $SERVICE_NAME --region $REGION --project $PROJECT --format json | ConvertFrom-Json
    if ($revisions) {
        $latest = $revisions[0]
        Write-Host "   Revision: $($latest.metadata.name)" -ForegroundColor Cyan
        Write-Host "   Status: $($latest.status.conditions[0].status)" -ForegroundColor Cyan
        Write-Host "   Created: $($latest.metadata.creationTimestamp)" -ForegroundColor Cyan
        Write-Host ""
        
        # Get logs
        Write-Host "3. Recent logs (last 20 lines):" -ForegroundColor Yellow
        Write-Host "   ----------------------------------------" -ForegroundColor Gray
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND resource.labels.revision_name=$($latest.metadata.name)" `
            --limit 20 `
            --format="value(textPayload)" `
            --project $PROJECT `
            --region $REGION | ForEach-Object { Write-Host "   $_" -ForegroundColor White }
    }
} else {
    Write-Host "   Service not found or not accessible!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available services:" -ForegroundColor Yellow
    gcloud run services list --region $REGION --project $PROJECT
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green

