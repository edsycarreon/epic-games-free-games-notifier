#!/bin/bash
# One-time setup for GCP deployment

PROJECT_ID="epic-games-free-games-bot"

echo "========================================="
echo "GCP Setup for Epic Games Notifier"
echo "========================================="
echo ""

# Set project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable APIs
echo ""
echo "Enabling required APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com

# Discord webhook
echo ""
echo "========================================="
echo "Discord Webhook Setup"
echo "========================================="
echo ""
echo "Enter your Discord webhook URL:"
read -r WEBHOOK_URL

if [ -n "$WEBHOOK_URL" ]; then
    echo ""
    echo "Creating secret..."
    echo -n "$WEBHOOK_URL" | gcloud secrets create discord-webhook-url --data-file=- 2>/dev/null || \
    echo -n "$WEBHOOK_URL" | gcloud secrets versions add discord-webhook-url --data-file=-
    
    echo "Granting Cloud Run access..."
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    gcloud secrets add-iam-policy-binding discord-webhook-url \
      --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor"
    
    echo ""
    echo "✓ Discord webhook configured"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Connect your repository in Cloud Build Console:"
echo "   https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo ""
echo "2. Create a trigger for push to 'main' branch using cloudbuild.yaml"
echo ""
echo "3. Push to deploy:"
echo "   git push origin main"
echo ""
