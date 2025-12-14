# Epic Games Free Games Notifier - Deployment

Get Discord notifications for free games on Epic Games Store (Philippines region).

## Quick Start

### 1. Run Setup

```bash
./setup.sh
```

This will:
- Enable required GCP APIs
- Create Discord webhook secret
- Configure permissions

### 2. Connect Repository

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers?project=epic-games-free-games-bot)
2. Click **"Create Trigger"**
3. Connect your repository (GitHub/GitLab)
4. Configure trigger:
   - **Name**: `deploy-on-push`
   - **Event**: Push to a branch
   - **Branch**: `^main$`
   - **Build configuration**: Cloud Build configuration file
   - **Location**: `cloudbuild.yaml`
5. Click **"Create"**

### 3. Deploy

```bash
git push origin main
```

Done! Cloud Build will deploy everything.

## What Gets Deployed

- **Cloud Run service** (asia-southeast1)
  - Runs on demand, scales to zero
  - Configured for Philippines (PH)
  
- **Cloud Scheduler** (daily at 9 AM PHT)
  - Automatically checks for free games
  - Sends Discord notifications

## Configuration

Everything is in `cloudbuild.yaml`:
- Region: `asia-southeast1`
- Country: `PH` (Philippines)
- Schedule: `0 9 * * *` (9 AM PHT)

## Testing

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe epic-games-notifier \
  --region=asia-southeast1 \
  --format="value(status.url)")

# Test it
curl -X POST $SERVICE_URL/check
```

## View Logs

```bash
gcloud run services logs read epic-games-notifier --region=asia-southeast1
```

## Update Discord Webhook

```bash
echo -n "NEW_WEBHOOK_URL" | gcloud secrets versions add discord-webhook-url --data-file=-
git push origin main  # Redeploy
```

---

**That's it!** Just push to main to deploy changes.

See [DEPLOY.md](DEPLOY.md) for more details.
