# Google Cloud Platform Deployment Guide

This guide covers deploying the Epic Games Free Games Notifier to Google Cloud Run with Cloud Scheduler for automated daily checks.

## Architecture

```
┌─────────────────────┐
│  Cloud Scheduler    │ (Cron trigger - daily at 9 AM)
└──────────┬──────────┘
           │ POST /check
           ▼
┌─────────────────────┐
│    Cloud Run        │ (HTTP server)
│  - Health check: /  │
│  - Trigger: /check  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Epic Games API     │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Discord Webhook    │
└─────────────────────┘
```

## Prerequisites

1. **Google Cloud Platform Account**
   - Active GCP project
   - Billing enabled

2. **Local Tools**
   - [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and configured
   - Docker installed
   - Bash shell

3. **Discord Webhook URL**
   - Create a webhook in your Discord server
   - Settings → Integrations → Webhooks → New Webhook

## Quick Deployment

### 1. Set Environment Variables

```bash
export GCP_PROJECT_ID="your-gcp-project-id"
export GCP_REGION="us-central1"  # Optional, defaults to us-central1
```

### 2. Store Discord Webhook in Secret Manager

```bash
# Create the secret
echo -n 'https://discord.com/api/webhooks/YOUR_WEBHOOK_URL' | \
  gcloud secrets create discord-webhook-url \
  --project="$GCP_PROJECT_ID" \
  --data-file=-

# Grant Cloud Run access to the secret
PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')

gcloud secrets add-iam-policy-binding discord-webhook-url \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Deploy

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- Enable required GCP APIs
- Build and push Docker image to GCR
- Deploy to Cloud Run
- Create/update Cloud Scheduler job

## Manual Deployment Steps

If you prefer manual deployment:

### 1. Enable APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Build and Push Image

```bash
# Set variables
PROJECT_ID="your-gcp-project-id"
SERVICE_NAME="epic-games-notifier"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Build
docker build -t "${IMAGE_NAME}:latest" .

# Configure Docker for GCR
gcloud auth configure-docker

# Push
docker push "${IMAGE_NAME}:latest"
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy epic-games-notifier \
  --image="gcr.io/${PROJECT_ID}/epic-games-notifier:latest" \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --max-instances=1 \
  --min-instances=0 \
  --set-env-vars="EPIC_LOCALE=en-US,EPIC_COUNTRY=US" \
  --set-secrets="DISCORD_WEBHOOK_URL=discord-webhook-url:latest"
```

### 4. Create Cloud Scheduler Job

```bash
# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe epic-games-notifier \
  --region=us-central1 \
  --format='value(status.url)')

# Create scheduler job
gcloud scheduler jobs create http epic-games-notifier-daily-check \
  --location=us-central1 \
  --schedule="0 9 * * *" \
  --uri="${SERVICE_URL}/check" \
  --http-method=POST \
  --time-zone="America/New_York" \
  --description="Daily check for Epic Games free games"
```

## Configuration

### Environment Variables

Set via Cloud Run deployment:

```bash
--set-env-vars="EPIC_LOCALE=en-US,EPIC_COUNTRY=US"
```

Available variables:
- `EPIC_LOCALE` - Game information locale (default: en-US)
- `EPIC_COUNTRY` - Country code (default: US)
- `DISCORD_WEBHOOK_URL` - Discord webhook URL (use Secret Manager)
- `DISCORD_MENTION_ROLE_ID` - Optional role ID to mention

### Secrets Management

Store sensitive data in Secret Manager:

```bash
# Create secret
echo -n 'secret-value' | gcloud secrets create secret-name --data-file=-

# Update secret
echo -n 'new-value' | gcloud secrets versions add secret-name --data-file=-

# Use in Cloud Run
gcloud run services update epic-games-notifier \
  --region=us-central1 \
  --set-secrets="ENV_VAR=secret-name:latest"
```

### Scheduler Configuration

Modify schedule (cron format):

```bash
# Daily at 9 AM
--schedule="0 9 * * *"

# Every Thursday at 10 AM (Epic's typical free game day)
--schedule="0 10 * * 4"

# Twice daily (9 AM and 5 PM)
--schedule="0 9,17 * * *"

# Every 6 hours
--schedule="0 */6 * * *"
```

Time zones:
```bash
--time-zone="America/New_York"    # EST/EDT
--time-zone="America/Los_Angeles" # PST/PDT
--time-zone="Europe/London"       # GMT/BST
--time-zone="UTC"                 # UTC
```

## Testing

### Test Health Check

```bash
SERVICE_URL=$(gcloud run services describe epic-games-notifier \
  --region=us-central1 \
  --format='value(status.url)')

curl "${SERVICE_URL}/health"
# Expected: {"status": "healthy"}
```

### Test Game Check

```bash
curl -X POST "${SERVICE_URL}/check"
# Expected: {"status": "Success: X active, Y upcoming"}
```

### Manually Trigger Scheduler

```bash
gcloud scheduler jobs run epic-games-notifier-daily-check \
  --location=us-central1
```

### View Logs

```bash
# Real-time logs
gcloud run logs tail epic-games-notifier --region=us-central1

# Recent logs
gcloud run logs read epic-games-notifier --region=us-central1 --limit=50

# Filter logs
gcloud run logs read epic-games-notifier \
  --region=us-central1 \
  --filter='severity>=ERROR'
```

## Local Testing with Docker

### Test Locally

```bash
# Build image
docker build -t epic-games-notifier:local .

# Run container
docker run -p 8080:8080 \
  -e DISCORD_WEBHOOK_URL='your-webhook-url' \
  -e EPIC_LOCALE='en-US' \
  -e EPIC_COUNTRY='US' \
  epic-games-notifier:local

# Test endpoints
curl http://localhost:8080/health
curl -X POST http://localhost:8080/check
```

### Use Docker Compose

```bash
# Create .env file
cp .env.example .env
# Edit .env with your Discord webhook URL

# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Test
curl http://localhost:8080/health
curl -X POST http://localhost:8080/check

# Stop service
docker-compose down
```

## Monitoring

### Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on `epic-games-notifier`
3. View metrics:
   - Request count
   - Request latency
   - Container instances
   - Error rate

### Set Up Alerts

```bash
# Create alerting policy for errors
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Epic Games Notifier Errors" \
  --condition-display-name="Error rate high" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s
```

## Cost Optimization

### Current Configuration

- **Memory**: 512Mi
- **CPU**: 1 vCPU
- **Min instances**: 0 (scales to zero when not in use)
- **Max instances**: 1 (sufficient for scheduled tasks)
- **Timeout**: 300s (5 minutes)

### Estimated Costs

With daily execution (once per day):
- **Cloud Run**: ~$0.10/month (mostly free tier)
- **Cloud Scheduler**: $0.10/month per job
- **Container Registry**: ~$0.05/month

**Total**: ~$0.25/month

### Reduce Costs

1. **Use Artifact Registry** (cheaper than GCR)
2. **Reduce memory** to 256Mi if sufficient
3. **Shorter timeout** if checks complete faster
4. **Clean old images** from registry

```bash
# List images
gcloud container images list --repository=gcr.io/$PROJECT_ID

# Delete old images
gcloud container images delete gcr.io/$PROJECT_ID/epic-games-notifier:OLD_TAG
```

## Troubleshooting

### Deployment Fails

```bash
# Check service status
gcloud run services describe epic-games-notifier --region=us-central1

# Check recent deployments
gcloud run revisions list --service=epic-games-notifier --region=us-central1

# View build logs
gcloud builds list --limit=5
```

### Container Won't Start

```bash
# Test container locally
docker run -p 8080:8080 gcr.io/$PROJECT_ID/epic-games-notifier:latest

# Check logs
docker logs CONTAINER_ID
```

### Scheduler Not Triggering

```bash
# Check job status
gcloud scheduler jobs describe epic-games-notifier-daily-check \
  --location=us-central1

# View job execution history
gcloud scheduler jobs describe epic-games-notifier-daily-check \
  --location=us-central1 \
  --format='value(status.lastAttemptTime)'

# Check scheduler logs
gcloud logging read "resource.type=cloud_scheduler_job" --limit=10
```

### Discord Notifications Not Sending

```bash
# Verify secret is accessible
gcloud secrets versions access latest --secret=discord-webhook-url

# Check Cloud Run has permission
gcloud secrets get-iam-policy discord-webhook-url

# Test webhook manually
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"Test message"}' \
  YOUR_WEBHOOK_URL
```

## Updating the Application

### Update Code

```bash
# Make changes to code
# Then redeploy
./deploy.sh
```

### Update Configuration

```bash
# Update environment variables
gcloud run services update epic-games-notifier \
  --region=us-central1 \
  --set-env-vars="EPIC_LOCALE=es-ES,EPIC_COUNTRY=ES"

# Update secrets
echo -n 'new-webhook-url' | \
  gcloud secrets versions add discord-webhook-url --data-file=-
```

### Update Schedule

```bash
# Update scheduler job
gcloud scheduler jobs update http epic-games-notifier-daily-check \
  --location=us-central1 \
  --schedule="0 10 * * 4"  # Thursday at 10 AM
```

## Cleanup

### Delete All Resources

```bash
# Delete Cloud Run service
gcloud run services delete epic-games-notifier --region=us-central1

# Delete Cloud Scheduler job
gcloud scheduler jobs delete epic-games-notifier-daily-check \
  --location=us-central1

# Delete secrets
gcloud secrets delete discord-webhook-url

# Delete container images
gcloud container images delete gcr.io/$PROJECT_ID/epic-games-notifier:latest
```

## Security Best Practices

1. **Use Secret Manager** for sensitive data (webhooks, API keys)
2. **Principle of least privilege** - only grant necessary permissions
3. **Enable VPC** for private networking (optional)
4. **Use service accounts** with minimal permissions
5. **Regularly update** dependencies and base images
6. **Monitor logs** for suspicious activity
7. **Enable Cloud Armor** for DDoS protection (optional)

## Advanced Configuration

### Use Artifact Registry (Recommended)

```bash
# Enable API
gcloud services enable artifactregistry.googleapis.com

# Create repository
gcloud artifacts repositories create epic-games-notifier \
  --repository-format=docker \
  --location=us-central1

# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Update IMAGE_NAME in deploy.sh to:
# IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/epic-games-notifier/${SERVICE_NAME}"
```

### Multiple Environments

```bash
# Deploy staging
gcloud run deploy epic-games-notifier-staging \
  --image=gcr.io/$PROJECT_ID/epic-games-notifier:staging \
  --region=us-central1

# Deploy production
gcloud run deploy epic-games-notifier-prod \
  --image=gcr.io/$PROJECT_ID/epic-games-notifier:latest \
  --region=us-central1
```

### Traffic Splitting (Blue/Green)

```bash
# Deploy new revision without traffic
gcloud run deploy epic-games-notifier \
  --image=gcr.io/$PROJECT_ID/epic-games-notifier:v2 \
  --region=us-central1 \
  --no-traffic

# Gradually shift traffic
gcloud run services update-traffic epic-games-notifier \
  --region=us-central1 \
  --to-revisions=LATEST=50,PREVIOUS=50
```

## Support

For issues or questions:
- Check logs: `gcloud run logs read epic-games-notifier --region=us-central1`
- Review [Cloud Run documentation](https://cloud.google.com/run/docs)
- Check [Cloud Scheduler documentation](https://cloud.google.com/scheduler/docs)
