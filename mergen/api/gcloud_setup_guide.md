# gcloud CLI Setup Guide

## Mevcut Yapılandırma

Mevcut yapılandırmanız zaten doğru görünüyor:
- **Project**: gen-lang-client-0307562385 ✅
- **Account**: arl.zgr@gmail.com ✅

## Yapılandırma Seçenekleri

### Seçenek 1: Mevcut Yapılandırmayı Kullan (Önerilen)

Eğer yapılandırma penceresi açıksa:
1. **Çıkış yapın** (Ctrl+C veya pencereyi kapatın)
2. Mevcut yapılandırma zaten doğru, deploy komutunu çalıştırabilirsiniz

### Seçenek 2: Yapılandırmayı Doğrulayın

Terminal'de şu komutları çalıştırın:

```powershell
# Mevcut yapılandırmayı kontrol et
gcloud config list

# Proje doğru mu kontrol et
gcloud config get-value project

# Eğer farklıysa, projeyi ayarla
gcloud config set project gen-lang-client-0307562385
```

## Deploy Komutu

Yapılandırma doğrulandıktan sonra deploy komutunu çalıştırın:

```powershell
cd d:\Mergenlite

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
  --add-cloudsql-instances gen-lang-client-0307562385:europe-west1:mergenlite-db `
  --set-env-vars "PORT=8080,OPENAI_API_KEY=YOUR_OPENAI_API_KEY,AMADEUS_API_KEY=mA1DG4KGPryyvo9AyMztUOvEb4lhxrjV,AMADEUS_API_SECRET=wrQkpsgfZWNH24nD,AMADEUS_ENV=production,POSTGRES_HOST=gen-lang-client-0307562385:europe-west1:mergenlite-db,POSTGRES_USER=postgres,POSTGRES_PASSWORD=YOUR_DB_PASSWORD,POSTGRES_DB=ZGR_AI,POSTGRES_PORT=5432,SMTP_HOST=smtp.gmail.com,SMTP_PORT=587,SMTP_USERNAME=arl.zgr@gmail.com,SMTP_PASSWORD=yaua qkmg xrqi slea,SMTP_USE_TLS=true"
```

**ÖNEMLİ**: `YOUR_DB_PASSWORD` yerine Cloud SQL şifrenizi yazın!

