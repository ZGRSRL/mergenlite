# Quick Deploy Script - Minimal Configuration
# Cloud SQL password'i buraya ekleyin

$DB_PASSWORD = "YOUR_DB_PASSWORD_HERE"  # <-- BURAYA CLOUD SQL SIFRESINI YAZIN
$CONN_NAME = "gen-lang-client-0307562385:europe-west1:mergenlite-db"

Write-Host "Deploying to Cloud Run..." -ForegroundColor Green

gcloud run deploy mergenlite-backend `
  --source ./mergen/api `
  --platform managed `
  --region europe-west1 `
  --allow-unauthenticated `
  --port 8080 `
  --timeout 3600 `
  --memory 2Gi `
  --cpu 2 `
  --max-instances 10 `
  --add-cloudsql-instances $CONN_NAME `
  --set-env-vars "PORT=8080,OPENAI_API_KEY=YOUR_OPENAI_API_KEY,AMADEUS_API_KEY=mA1DG4KGPryyvo9AyMztUOvEb4lhxrjV,AMADEUS_API_SECRET=wrQkpsgfZWNH24nD,AMADEUS_ENV=production,POSTGRES_HOST=$CONN_NAME,POSTGRES_USER=postgres,POSTGRES_PASSWORD=$DB_PASSWORD,POSTGRES_DB=ZGR_AI,POSTGRES_PORT=5432,SMTP_HOST=smtp.gmail.com,SMTP_PORT=587,SMTP_USERNAME=arl.zgr@gmail.com,SMTP_PASSWORD=yaua qkmg xrqi slea,SMTP_USE_TLS=true"

Write-Host ""
Write-Host "Deployment complete! Check logs if there are any issues." -ForegroundColor Green

