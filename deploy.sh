#!/bin/bash
# Deployment script for Google Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-gcp-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-epic-games-notifier}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Epic Games Free Games Notifier - Cloud Run Deployment ===${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Validate project ID
if [ "$PROJECT_ID" = "your-gcp-project-id" ]; then
    echo -e "${RED}Error: Please set GCP_PROJECT_ID environment variable${NC}"
    echo "Example: export GCP_PROJECT_ID=my-project-123"
    exit 1
fi

# Set the active project
echo -e "${YELLOW}Setting active GCP project to: ${PROJECT_ID}${NC}"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo -e "${YELLOW}Enabling required GCP APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com

# Build and push the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t "${IMAGE_NAME}:latest" .

echo -e "${YELLOW}Pushing image to Google Container Registry...${NC}"
docker push "${IMAGE_NAME}:latest"

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"

# Check if Discord webhook secret exists
if gcloud secrets describe discord-webhook-url --project="$PROJECT_ID" &> /dev/null; then
    SECRET_FLAG="--set-secrets=DISCORD_WEBHOOK_URL=discord-webhook-url:latest"
    echo -e "${GREEN}Using Discord webhook from Secret Manager${NC}"
else
    SECRET_FLAG=""
    echo -e "${YELLOW}Warning: discord-webhook-url secret not found in Secret Manager${NC}"
    echo "To create it, run:"
    echo "  echo -n 'YOUR_WEBHOOK_URL' | gcloud secrets create discord-webhook-url --data-file=-"
fi

gcloud run deploy "$SERVICE_NAME" \
    --image="${IMAGE_NAME}:latest" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --max-instances=1 \
    --min-instances=0 \
    --set-env-vars="EPIC_LOCALE=en-US,EPIC_COUNTRY=US" \
    $SECRET_FLAG

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --format='value(status.url)')

echo -e "${GREEN}Service deployed successfully!${NC}"
echo -e "Service URL: ${SERVICE_URL}"

# Create Cloud Scheduler job
echo -e "${YELLOW}Setting up Cloud Scheduler...${NC}"

JOB_NAME="${SERVICE_NAME}-daily-check"
SCHEDULE="0 9 * * *"  # Daily at 9 AM

# Check if job exists
if gcloud scheduler jobs describe "$JOB_NAME" --location="$REGION" &> /dev/null; then
    echo -e "${YELLOW}Updating existing Cloud Scheduler job...${NC}"
    gcloud scheduler jobs update http "$JOB_NAME" \
        --location="$REGION" \
        --schedule="$SCHEDULE" \
        --uri="${SERVICE_URL}/check" \
        --http-method=POST \
        --time-zone="America/New_York"
else
    echo -e "${YELLOW}Creating new Cloud Scheduler job...${NC}"
    gcloud scheduler jobs create http "$JOB_NAME" \
        --location="$REGION" \
        --schedule="$SCHEDULE" \
        --uri="${SERVICE_URL}/check" \
        --http-method=POST \
        --time-zone="America/New_York" \
        --description="Daily check for Epic Games free games"
fi

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Service URL: ${SERVICE_URL}"
echo "Health check: ${SERVICE_URL}/health"
echo "Trigger check: ${SERVICE_URL}/check"
echo ""
echo "Cloud Scheduler job: $JOB_NAME"
echo "Schedule: $SCHEDULE (Daily at 9 AM)"
echo ""
echo -e "${GREEN}To test the deployment:${NC}"
echo "  curl ${SERVICE_URL}/health"
echo "  curl -X POST ${SERVICE_URL}/check"
echo ""
echo -e "${GREEN}To view logs:${NC}"
echo "  gcloud run logs read $SERVICE_NAME --region=$REGION"
echo ""
echo -e "${GREEN}To manually trigger the scheduler:${NC}"
echo "  gcloud scheduler jobs run $JOB_NAME --location=$REGION"
