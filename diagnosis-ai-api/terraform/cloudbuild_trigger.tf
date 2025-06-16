resource "google_service_account" "cloud_build_sa" {
  account_id   = "${var.app_name}-cloud-build"
  display_name = "Cloud build Service Account for ${var.app_name}"
}

# artifact registry 編集権限
resource "google_project_iam_member" "artifact_registry_editor" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cloud_build_sa.email}"
}

# Cloud Logging 書き込み権限を追加
resource "google_project_iam_member" "cloudbuild_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_build_sa.email}"
}

# Cloud Logging 閲覧権限を追加
resource "google_project_iam_member" "cloudbuild_logging_viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.cloud_build_sa.email}"
}

# Grant Cloud Run admin permissions to the build SA so it can update services
resource "google_project_iam_member" "cloud_build_sa_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cloud_build_sa.email}"
}

resource "google_cloudbuild_trigger" "mbti-diagnosis-api-github-trigger" {
  name = "mbti-diagnosis-api-github-trigger"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  included_files = ["diagnosis-ai-api/**"]
  ignored_files  = ["README.md", "docs/**"]

  filename        = "diagnosis-ai-api/terraform/yaml/cloudbuild.yaml"
  service_account = google_service_account.cloud_build_sa.id

  substitutions = {
    _AR_HOSTNAME   = var.ar_hostname
    _AR_PROJECT_ID = var.project_id
    _AR_REPOSITORY = var.ar_repository
    _SERVICE_NAME  = var.app_name
    _DEPLOY_REGION = var.region
    REPO_NAME      = lower(var.github_repo)
  }

  depends_on = [
    google_project_iam_member.artifact_registry_editor,
    google_project_iam_member.cloudbuild_logging_writer
  ]
}
