# 🚀 Quick Start - 3 Steps to Deploy

## Step 1: Run Setup Script

```bash
./setup.sh
```

This enables the required GCP APIs.

## Step 2: Create Cloud Build Trigger

1. Go to: https://console.cloud.google.com/cloud-build/triggers?project=epic-games-free-games-bot

2. Click **"CREATE TRIGGER"**

3. **Source**:
   - Connect your repository (GitHub/GitLab)
   - Select this repository

4. **Configuration**:
   - Name: `deploy-on-push`
   - Event: **Push to a branch**
   - Branch: `^main$`
   - Type: **Cloud Build configuration file**
   - Location: `cloudbuild.yaml`

5. **Substitution variables** (expand "Show advanced"):

   Add these 3 variables:

   | Variable | Value |
   |----------|-------|
   | `_DISCORD_WEBHOOK_URL` | Your Discord webhook URL |
   | `_EPIC_LOCALE` | `en-US` |
   | `_EPIC_COUNTRY` | `PH` |

   Example:
   ```
   _DISCORD_WEBHOOK_URL = https://discord.com/api/webhooks/1234567890/abcdefg...
   _EPIC_LOCALE = en-US
   _EPIC_COUNTRY = PH
   ```

6. Click **"CREATE"**

## Step 3: Deploy

```bash
git push origin main
```

That's it! Cloud Build will:
- ✅ Build the Docker image
- ✅ Deploy to Cloud Run
- ✅ Set up Cloud Scheduler (9 AM PHT daily)

## Test Your Deployment

```bash
# Get your service URL
SERVICE_URL=$(gcloud run services describe epic-games-notifier \
  --region=asia-southeast1 \
  --format="value(status.url)")

# Test it (should send Discord notification)
curl -X POST $SERVICE_URL/check
```

## View Logs

```bash
gcloud run services logs read epic-games-notifier --region=asia-southeast1
```

---

**🎉 Done!** Your bot is now live and will check daily at 9 AM PHT.

Need help? See [DEPLOY.md](DEPLOY.md) for more details.
