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
  cloudscheduler.googleapis.com

echo ""
echo "✓ APIs enabled"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Connect your repository in Cloud Build Console:"
echo "   https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo ""
echo "2. Create a trigger for push to 'main' branch using cloudbuild.yaml"
echo ""
echo "3. Add substitution variables in the trigger:"
echo "   _DISCORD_WEBHOOK_URL = YOUR_DISCORD_WEBHOOK_URL"
echo "   _EPIC_LOCALE = en-US"
echo "   _EPIC_COUNTRY = PH"
echo ""
echo "4. Push to deploy:"
echo "   git push origin main"
echo ""
