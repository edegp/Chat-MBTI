#!/bin/bash

# Cloud Run deployment script for MBTI Diagnosis API
set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-"your-project-id"}
REGION=${REGION:-"asia-northeast1"}
SERVICE_NAME=${SERVICE_NAME:-"mbti-diagnosis-api"}
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}-repo/${SERVICE_NAME}"

echo "🚀 Starting deployment to Google Cloud Run..."
echo "📋 Configuration:"
echo "   Project ID: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service Name: ${SERVICE_NAME}"
echo "   Image: ${IMAGE_NAME}"

# Check if required environment variables are set
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "❌ Error: PROJECT_ID environment variable is not set"
    echo "   Please set it with: export PROJECT_ID=your-actual-project-id"
    exit 1
fi

# Set the current project
echo "🔧 Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Configure Docker authentication
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push the Docker image
echo "🏗️  Building Docker image..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:latest .

echo "📤 Pushing image to Artifact Registry..."
docker push ${IMAGE_NAME}:latest

echo "✅ Image pushed successfully!"
echo "🔄 You can now run 'terraform apply' to deploy the infrastructure and service."
echo ""
echo "💡 Next steps:"
echo "   1. Make sure your terraform.tfvars file is configured"
echo "   2. Run: cd terraform && terraform init"
echo "   3. Run: terraform plan"
echo "   4. Run: terraform apply"
