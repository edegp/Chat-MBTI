# Google Cloud Provider configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "servicenetworking.googleapis.com",
    "secretmanager.googleapis.com"
  ])

  service = each.value
  project = var.project_id

  disable_dependent_services = true
}

# Create Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "${var.app_name}-repo"
  description   = "Docker repository for ${var.app_name}"
  format        = "DOCKER"

  depends_on = [google_project_service.required_apis]
}


#
# Import existing Cloud Run service instead of creating new one
# The actual Cloud Run service "chat-mbti" will be managed externally
# We only manage the infrastructure it depends on (SQL, secrets, etc.)

# Make the service publicly accessible
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = "chat-mbti"
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
