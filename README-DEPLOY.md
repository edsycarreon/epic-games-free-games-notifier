# Epic Games Free Games Notifier - Deployment

Get Discord notifications for free games on Epic Games Store (Philippines region).

## Quick Start

### 1. Run Setup

```bash
./setup.sh
```

This will:
- Enable required GCP APIs
- Configure project settings

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
5. Add **Substitution variables** (click "Show advanced"):
   - `_DISCORD_WEBHOOK_URL` = Your Discord webhook URL
   - `_EPIC_LOCALE` = `en-US`
   - `_EPIC_COUNTRY` = `PH`
6. Click **"Create"**

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

Set via Cloud Build substitution variables:
- `_DISCORD_WEBHOOK_URL` - Your Discord webhook
- `_EPIC_LOCALE` - `en-US`
- `_EPIC_COUNTRY` - `PH` (Philippines)

Deployment settings:
- Region: `asia-southeast1`
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

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers?project=epic-games-free-games-bot)
2. Click on your trigger
3. Click **"Edit"**
4. Update the `_DISCORD_WEBHOOK_URL` substitution variable
5. Click **"Save"**
6. Push to redeploy: `git push origin main`

---

**That's it!** Just push to main to deploy changes.

See [DEPLOY.md](DEPLOY.md) for more details.
