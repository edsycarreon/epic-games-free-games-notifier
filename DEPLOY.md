# GCP Deployment Guide

Simple deployment using Cloud Build - just push to main and it deploys automatically.

## One-Time Setup

### 1. Create Discord Webhook Secret

```bash
# Set your project
gcloud config set project epic-games-free-games-bot

# Create the secret with your Discord webhook URL
echo -n "YOUR_DISCORD_WEBHOOK_URL" | gcloud secrets create discord-webhook-url --data-file=-

# Grant Cloud Run access to the secret
PROJECT_NUMBER=$(gcloud projects describe epic-games-free-games-bot --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding discord-webhook-url \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 2. Enable Required APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com
```

### 3. Connect Repository to Cloud Build

Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers) and:

1. Click "Connect Repository"
2. Select your source (GitHub/GitLab/etc)
3. Authenticate and select this repository
4. Create a trigger with:
   - **Name**: `deploy-on-push`
   - **Event**: Push to branch
   - **Branch**: `^main$`
   - **Build configuration**: Cloud Build configuration file
   - **Location**: `cloudbuild.yaml`

## Deploy

Just push to main:

```bash
git add .
git commit -m "deploy: update application"
git push origin main
```

Cloud Build will automatically:
- Build the Docker image
- Deploy to Cloud Run (asia-southeast1)
- Update Cloud Scheduler to run daily at 9 AM PHT

## Configuration

All configuration is in `cloudbuild.yaml`:

- **Region**: `asia-southeast1`
- **Environment**: `EPIC_COUNTRY=PH`, `EPIC_LOCALE=en-US`
- **Schedule**: Daily at 9 AM PHT (Asia/Manila timezone)
- **Memory**: 512MB
- **Timeout**: 5 minutes

## Manual Trigger (Optional)

To manually trigger a build without pushing:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

## View Logs

```bash
# Cloud Build logs
gcloud builds list --limit=5

# Cloud Run logs
gcloud run services logs read epic-games-notifier --region=asia-southeast1 --limit=50
```

## Test Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe epic-games-notifier \
  --region=asia-southeast1 \
  --format="value(status.url)")

# Test health
curl $SERVICE_URL/health

# Test game check (triggers Discord notification)
curl -X POST $SERVICE_URL/check
```

## Update Discord Webhook

```bash
echo -n "NEW_WEBHOOK_URL" | gcloud secrets versions add discord-webhook-url --data-file=-
```

Then redeploy by pushing to main.

---

That's it! Push to main = deployed.
