# output "cloud_run_url" {
#   description = "URL of the deployed Cloud Run service"
#   value       = google_cloud_run_v2_service.main.uri
# }

# output "cloud_run_service_name" {
#   description = "Name of the Cloud Run service"
#   value       = google_cloud_run_v2_service.main.name
# }

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "asia-northeast1-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.cloud_run_sa.email
}

output "secret_manager_secrets" {
  description = "Secret Manager secret IDs"
  value = {
    gemini_api_key = google_secret_manager_secret.gemini_api_key.secret_id
    database_url   = google_secret_manager_secret.database_url.secret_id
  }
}
