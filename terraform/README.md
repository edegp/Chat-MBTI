# MBTI Diagnosis API - Cloud Run Deployment

This directory contains Terraform configuration for deploying the MBTI Diagnosis API to Google Cloud Run.

## Prerequisites

1. **Google Cloud SDK**: Install and configure `gcloud` CLI
2. **Terraform**: Install Terraform (>= 1.0)
3. **Docker**: Install Docker for building images
4. **Google Cloud Project**: Create a GCP project with billing enabled

## Setup Instructions

### 1. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  servicenetworking.googleapis.com \
  secretmanager.googleapis.com
```

### 2. Configure Terraform Variables

Copy the example variables file and fill in your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your specific values:

```hcl
project_id = "your-gcp-project-id"
db_password = "your-secure-database-password"
gemini_api_key = "your-gemini-api-key"

# Optional customizations
region = "asia-northeast1"
app_name = "mbti-diagnosis-api"
min_instances = 0
max_instances = 10
cpu_limit = "1"
memory_limit = "2Gi"
```

### 3. Build and Push Docker Image

Set your project ID and run the deployment script:

```bash
export PROJECT_ID=your-project-id
./deploy.sh
```

This script will:

- Configure Docker authentication
- Build the Docker image
- Push it to Google Artifact Registry

### 4. Deploy Infrastructure

Initialize and apply Terraform:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Architecture Overview

The deployment creates:

- **Cloud Run Service**: Main API service with auto-scaling
- **Cloud SQL (PostgreSQL)**: Database for LangGraph checkpoints
- **Artifact Registry**: Docker image repository
- **Service Account**: With minimal required permissions
- **Secret Manager**: For sensitive configuration (API keys, DB credentials)

## Configuration

### Environment Variables

The Cloud Run service is configured with these environment variables:

- `PORT`: 8000
- `DATABASE_URL`: PostgreSQL connection string (from Secret Manager)
- `GEMINI_API_KEY`: Google Gemini API key (from Secret Manager)
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `LANGSMITH_TRACING`: true
- `LANGSMITH_PROJECT`: App name for tracing

### Resources

Default resource limits:

- **CPU**: 1 vCPU
- **Memory**: 2 GiB
- **Instances**: 0-10 (auto-scaling)

### Database

- **Engine**: PostgreSQL 15
- **Tier**: db-f1-micro (adjustable)
- **Storage**: 20GB SSD with auto-resize
- **Backup**: Daily at 3:00 AM with point-in-time recovery

## Security

- Service account with minimal permissions
- Secrets stored in Google Secret Manager
- Database credentials encrypted
- API keys protected
- Cloud SQL with authorized networks

## Monitoring

After deployment, you can monitor your service:

```bash
# View logs
gcloud run services logs tail mbti-diagnosis-api --region=asia-northeast1

# Check service status
gcloud run services describe mbti-diagnosis-api --region=asia-northeast1
```

## Outputs

After successful deployment, Terraform will output:

- `cloud_run_url`: Your API endpoint URL
- `artifact_registry_repository`: Docker repository URL
- `database_connection_name`: Cloud SQL connection name
- `service_account_email`: Service account email

## Updating the Service

To update your service:

1. Make code changes
2. Run `./deploy.sh` to build and push new image
3. Run `terraform apply` to update the service

## Cost Optimization

For production use, consider:

- Adjusting `min_instances` to reduce cold starts
- Using larger `db_tier` for better performance
- Setting up monitoring and alerting
- Implementing proper CORS policies
- Adding custom domain with SSL

## Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure your user has necessary IAM roles
2. **API Not Enabled**: Run the API enablement commands above
3. **Image Not Found**: Make sure `./deploy.sh` completed successfully
4. **Database Connection**: Check Cloud SQL instance is running and accessible

### Debug Commands

```bash
# Check Cloud Run service
gcloud run services list

# Check database status
gcloud sql instances list

# View recent logs
gcloud run services logs tail mbti-diagnosis-api --limit=50
```
