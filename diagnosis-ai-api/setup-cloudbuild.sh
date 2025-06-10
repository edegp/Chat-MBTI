#!/bin/bash

# Cloud Build GitHub trigger setup script
set -e

PROJECT_ID=${PROJECT_ID:-"chat-mbti-458210"}
REGION=${REGION:-"asia-northeast1"}
SERVICE_NAME=${SERVICE_NAME:-"mbti-diagnosis-api"}
GITHUB_OWNER=${GITHUB_OWNER:-"edegp"}
GITHUB_REPO=${GITHUB_REPO:-"Chat-MBTI"}
GITHUB_BRANCH=${GITHUB_BRANCH:-"main"}

echo "🔧 Setting up Cloud Build GitHub trigger..."
echo "📋 Configuration:"
echo "   Project ID: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service Name: ${SERVICE_NAME}"
echo "   GitHub Repository: ${GITHUB_OWNER}/${GITHUB_REPO}"
echo "   Branch: ${GITHUB_BRANCH}"

# Check if required environment variables are set
if [ -z "$GITHUB_OWNER" ] || [ "$GITHUB_OWNER" = "your-github-username" ]; then
    echo "❌ Error: GITHUB_OWNER environment variable is not set properly"
    echo "   Current value: ${GITHUB_OWNER}"
    echo "   Please set it with: export GITHUB_OWNER=your-actual-github-username"
    exit 1
fi

# Set the current project
echo "🔧 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Enable Cloud Build API
echo "📦 Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com

# Create Cloud Build trigger
echo "⚡ Creating Cloud Build trigger..."
gcloud builds triggers create github \
    --repo-name="${GITHUB_REPO}" \
    --repo-owner="${GITHUB_OWNER}" \
    --branch-pattern="^${GITHUB_BRANCH}$" \
    --build-config="diagnosis-ai-api/cloudbuild.yaml" \
    --name="${SERVICE_NAME}-github-trigger" \
    --description="Automatic deployment trigger for ${SERVICE_NAME}"

echo "✅ Cloud Build trigger created successfully!"
echo ""
echo "💡 To connect your GitHub repository:"
echo "   1. Go to: https://console.cloud.google.com/cloud-build/triggers"
echo "   2. Click on the trigger '${SERVICE_NAME}-github-trigger'"
echo "   3. Click 'Connect Repository' if not already connected"
echo "   4. Follow the GitHub OAuth flow to connect your repository"
echo ""
echo "🚀 Once connected, pushes to the '${GITHUB_BRANCH}' branch will automatically deploy your app!"
