# Cloud Run Logs Checker
# Usage: .\mergen\api\check_logs.ps1

$SERVICE_NAME = "mergenlite-backend"
$REGION = "europe-west1"
$PROJECT = "gen-lang-client-0307562385"

Write-Host "Fetching logs for: $SERVICE_NAME" -ForegroundColor Green
Write-Host ""

# Son 50 log satırını getir
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" `
  --limit 50 `
  --format="table(timestamp,severity,textPayload)" `
  --project=$PROJECT `
  --region=$REGION

Write-Host ""
Write-Host "For more logs, visit:" -ForegroundColor Yellow
Write-Host "https://console.cloud.google.com/logs/viewer?project=$PROJECT" -ForegroundColor Cyan

