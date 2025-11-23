# Cloud Scheduler Kurulum Rehberi

## Günlük Otomatik Analiz Sistemi

Bu sistem, her sabah belirli bir NAICS kodu (varsayılan: 721110 - Hotel/Motel) için SAM.gov'dan yeni ilanları çeker, analiz eder ve e-posta gönderir.

## Endpoint

### POST `/api/jobs/daily-scan`

Cloud Scheduler tarafından tetiklenen endpoint.

**Request Body:**
```json
{
  "target_id": "721110",
  "naics_code": "721110",
  "days_back": 1,
  "limit": 10,
  "force_refresh": false
}
```

**Response (202 Accepted):**
```json
{
  "status": "accepted",
  "message": "Günlük analiz başlatıldı. Hedef: NAICS 721110",
  "target_id": "721110",
  "naics_code": "721110",
  "days_back": 1,
  "limit": 10,
  "force_refresh": false
}
```

## Cloud Scheduler Kurulumu

### 1. Cloud Run Deploy Sonrası URL'i Al

```bash
gcloud run services describe mergenlite-backend \
  --region europe-west1 \
  --format="value(status.url)"
```

Örnek çıktı: `https://mergenlite-backend-xyz123.a.run.app`

### 2. Cloud Scheduler Job Oluştur

```bash
gcloud scheduler jobs create http daily-hotel-scan \
  --schedule "0 7 * * *" \
  --uri "https://mergenlite-backend-xyz123.a.run.app/api/jobs/daily-scan" \
  --http-method POST \
  --headers "Content-Type=application/json" \
  --message-body '{"naics_code": "721110", "days_back": 1, "limit": 10, "force_refresh": false}' \
  --time-zone "Europe/Istanbul" \
  --region europe-west1
```

### 3. Job'u Test Et

```bash
# Manuel tetikleme
gcloud scheduler jobs run daily-hotel-scan --region europe-west1
```

### 4. Job Durumunu Kontrol Et

```bash
# Job detayları
gcloud scheduler jobs describe daily-hotel-scan --region europe-west1

# Son çalışma geçmişi
gcloud scheduler jobs list --region europe-west1
```

## Zamanlama (Cron Format)

- `0 7 * * *` - Her gün saat 07:00 (Istanbul timezone)
- `0 8 * * *` - Her gün saat 08:00
- `0 */6 * * *` - Her 6 saatte bir
- `0 9 * * 1` - Her Pazartesi saat 09:00

## Durum Kontrolü

### GET `/api/jobs/daily-scan/status`

Son günlük tarama durumunu kontrol eder.

**Query Parameters:**
- `naics_code` (default: "721110")
- `days_back` (default: 1)

**Response:**
```json
{
  "naics_code": "721110",
  "days_back": 1,
  "opportunities_found": 5,
  "opportunities": [
    {
      "opportunity_id": 123,
      "notice_id": "ABC123",
      "title": "Hotel Services...",
      "posted_date": "2024-01-15T10:00:00",
      "analyses_count": 1,
      "latest_analysis": {
        "id": 456,
        "type": "sow_draft",
        "status": "completed",
        "created_at": "2024-01-15T10:05:00"
      }
    }
  ]
}
```

## Güvenlik

Cloud Scheduler'dan gelen istekleri doğrulamak için:

1. **Cloud Scheduler Authentication:** Cloud Scheduler otomatik olarak OIDC token ekler
2. **Service Account:** Cloud Run service'inin `cloud-scheduler-invoker` rolüne sahip olması gerekir

```bash
# Service account'a rol ver
gcloud run services add-iam-policy-binding mergenlite-backend \
  --member="serviceAccount:cloud-scheduler@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region europe-west1
```

## Troubleshooting

### Job çalışmıyor
- Cloud Scheduler loglarını kontrol et: `gcloud scheduler jobs describe daily-hotel-scan --region europe-west1`
- Cloud Run loglarını kontrol et: `gcloud run services logs read mergenlite-backend --region europe-west1`

### Timeout hatası
- Cloud Run timeout'u artır: `--timeout 3600` (1 saat)
- Background task kullanıldığı için endpoint hemen 202 döner, işlem arka planda devam eder

### İlan bulunamıyor
- SAM.gov API key'inin doğru olduğundan emin ol
- `days_back` parametresini artır (örn: 7 gün)
- NAICS kodunu kontrol et

