#!/bin/bash
# Cloud Run Deployment Script for MergenLite Backend
# Usage: ./cloud_run_deploy.sh

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="mergenlite-backend"
SOURCE_DIR="./mergen/api"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MergenLite Cloud Run Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}ERROR: gcloud CLI is not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}Not logged in to gcloud. Please run: gcloud auth login${NC}"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

echo ""
echo -e "${YELLOW}Required Environment Variables:${NC}"
echo "  - OPENAI_API_KEY (required for LLM)"
echo "  - AMADEUS_API_KEY (required for hotel search)"
echo "  - AMADEUS_API_SECRET (required for hotel search)"
echo "  - POSTGRES_HOST (Cloud SQL instance connection name)"
echo "  - POSTGRES_USER (database user)"
echo "  - POSTGRES_PASSWORD (database password)"
echo "  - POSTGRES_DB (database name)"
echo "  - SMTP_HOST (optional, for email notifications)"
echo "  - SMTP_USERNAME (optional)"
echo "  - SMTP_PASSWORD (optional)"
echo "  - PIPELINE_NOTIFICATION_EMAIL (optional)"
echo ""

# Read environment variables
read -p "Enter OPENAI_API_KEY: " OPENAI_API_KEY
read -p "Enter AMADEUS_API_KEY: " AMADEUS_API_KEY
read -s -p "Enter AMADEUS_API_SECRET: " AMADEUS_API_SECRET
echo ""
read -p "Enter POSTGRES_HOST (Cloud SQL connection name, e.g., project:region:instance): " POSTGRES_HOST
read -p "Enter POSTGRES_USER [postgres]: " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-postgres}
read -s -p "Enter POSTGRES_PASSWORD: " POSTGRES_PASSWORD
echo ""
read -p "Enter POSTGRES_DB [ZGR_AI]: " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-ZGR_AI}
read -p "Enter POSTGRES_PORT [5432]: " POSTGRES_PORT
POSTGRES_PORT=${POSTGRES_PORT:-5432}

# Optional SMTP settings
read -p "Enter SMTP_HOST (optional, press Enter to skip): " SMTP_HOST
if [ -n "$SMTP_HOST" ]; then
    read -p "Enter SMTP_USERNAME: " SMTP_USERNAME
    read -s -p "Enter SMTP_PASSWORD: " SMTP_PASSWORD
    echo ""
    read -p "Enter PIPELINE_NOTIFICATION_EMAIL: " PIPELINE_NOTIFICATION_EMAIL
fi

# Build environment variables string
ENV_VARS="OPENAI_API_KEY=${OPENAI_API_KEY}"
ENV_VARS="${ENV_VARS},AMADEUS_API_KEY=${AMADEUS_API_KEY}"
ENV_VARS="${ENV_VARS},AMADEUS_API_SECRET=${AMADEUS_API_SECRET}"
ENV_VARS="${ENV_VARS},POSTGRES_HOST=${POSTGRES_HOST}"
ENV_VARS="${ENV_VARS},POSTGRES_USER=${POSTGRES_USER}"
ENV_VARS="${ENV_VARS},POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
ENV_VARS="${ENV_VARS},POSTGRES_DB=${POSTGRES_DB}"
ENV_VARS="${ENV_VARS},POSTGRES_PORT=${POSTGRES_PORT}"
ENV_VARS="${ENV_VARS},AMADEUS_ENV=production"
ENV_VARS="${ENV_VARS},PORT=8080"

if [ -n "$SMTP_HOST" ]; then
    ENV_VARS="${ENV_VARS},SMTP_HOST=${SMTP_HOST}"
    ENV_VARS="${ENV_VARS},SMTP_USERNAME=${SMTP_USERNAME}"
    ENV_VARS="${ENV_VARS},SMTP_PASSWORD=${SMTP_PASSWORD}"
    ENV_VARS="${ENV_VARS},SMTP_PORT=587"
    ENV_VARS="${ENV_VARS},SMTP_USE_TLS=true"
    if [ -n "$PIPELINE_NOTIFICATION_EMAIL" ]; then
        ENV_VARS="${ENV_VARS},PIPELINE_NOTIFICATION_EMAIL=${PIPELINE_NOTIFICATION_EMAIL}"
    fi
fi

echo ""
echo -e "${GREEN}Deploying to Cloud Run...${NC}"
echo ""

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --source ${SOURCE_DIR} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "${ENV_VARS}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service URL:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)"
echo ""

