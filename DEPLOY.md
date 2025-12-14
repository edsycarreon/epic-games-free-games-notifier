# GCP Deployment Guide

Simple deployment using Cloud Build - just push to main and it deploys automatically.

## One-Time Setup

### 1. Enable Required APIs

```bash
# Set your project
gcloud config set project epic-games-free-games-bot

# Enable APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com
```

Or just run: `./setup.sh`

### 2. Connect Repository to Cloud Build

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
5. Add **Substitution variables**:
   - `_DISCORD_WEBHOOK_URL` = Your Discord webhook URL
   - `_EPIC_LOCALE` = `en-US`
   - `_EPIC_COUNTRY` = `PH`

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

All configuration is set via **Cloud Build substitution variables**:

- **Discord Webhook**: `_DISCORD_WEBHOOK_URL`
- **Locale**: `_EPIC_LOCALE` (default: `en-US`)
- **Country**: `_EPIC_COUNTRY` (default: `PH`)

Deployment settings in `cloudbuild.yaml`:
- **Region**: `asia-southeast1`
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

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click on your trigger → **Edit**
3. Update the `_DISCORD_WEBHOOK_URL` value
4. Click **Save**
5. Redeploy: `git push origin main`

---

That's it! Push to main = deployed.
