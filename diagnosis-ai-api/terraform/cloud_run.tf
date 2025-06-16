# Make the service publicly accessible
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  name     = var.app_name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
# Service account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.app_name}-cloud-run"
  display_name = "Cloud Run Service Account for ${var.app_name}"
}
#Grant necessary permissions to the service account
resource "google_project_iam_member" "cloud_run_sa_permissions" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/cloudsql.client",
    "roles/firebase.admin",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    "roles/vpcaccess.user"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

#     "roles/storage.legacyBucketWriter"
resource "google_storage_bucket_iam_member" "cloud_run_sa_storage_legacy_bucket_writer" {
  bucket = var.gcs_bucket_name
  role   = "roles/storage.legacyBucketWriter"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Allow Cloud Build service account to actAs the Cloud Run service account
resource "google_service_account_iam_member" "allow_build_act_as_run_sa" {
  service_account_id = google_service_account.cloud_run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloud_build_sa.email}"
}
resource "google_cloud_run_v2_service" "main" {
  name     = var.app_name
  location = "asia-northeast1"
  project  = "chat-mbti-458210"

  template {
    # Enable private VPC connectivity
    vpc_access {
      connector = "projects/${var.project_id}/locations/${var.region}/connectors/${var.vpc_connector_name}"
      egress    = "ALL_TRAFFIC"
    }
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/${lower(var.github_repo)}/${var.app_name}:latest"
      ports {
        name           = "http1"
        container_port = 8000
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "LANGSMITH_TRACING"
        value = "false"
      }
      env {
        name  = "DB_NAME"
        value = "mbti_diagnosis"
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "mbti-diagnosis-api-gemini-api-key"
            version = "latest"
          }
        }
      }
      env {
        name = "SQL_CONNECTION_NAME"
        value_source {
          secret_key_ref {
            secret  = "mbti-diagnosis-api-cloudsql-connection-name"
            version = "latest"
          }
        }
      }
      env {
        name = "DB_APP_USER"
        value_source {
          secret_key_ref {
            secret  = "mbti-diagnosis-api-db-app-user"
            version = "latest"
          }
        }
      }
      env {
        name = "DB_APP_PASS"
        value_source {
          secret_key_ref {
            secret  = "mbti-diagnosis-api-db-app-pass"
            version = "latest"
          }
        }
      }
      env {
        name = "DB_ADMIN_USER"
        value_source {
          secret_key_ref {
            secret  = "mbti-diagnosis-api-db-admin-user"
            version = "latest"
          }
        }
      }
      env {
        name = "DB_ADMIN_PASS"
        value_source {
          secret_key_ref {
            secret  = "mbti-diagnosis-api-db-admin-pass"
            version = "latest"
          }
        }
      }

      # GCS bucket name for data uploads
      env {
        name  = "GCS_BUCKET_NAME"
        value = var.gcs_bucket_name
      }
      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }
      startup_probe {
        timeout_seconds   = 240
        period_seconds    = 240
        failure_threshold = 1
        tcp_socket {
          port = 8000
        }
      }
    }
    max_instance_request_concurrency = 80
    service_account                  = google_service_account.cloud_run_sa.email
    # Cloud SQL接続
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = ["chat-mbti-458210:asia-northeast1:mbti-diagnosis-api-postgres"]
      }
    }
    annotations = {
      "autoscaling.knative.dev/maxScale"      = "100"
      "run.googleapis.com/startup-cpu-boost"  = "true"
      "run.googleapis.com/cloudsql-instances" = "chat-mbti-458210:asia-northeast1:mbti-diagnosis-api-postgres"
    }
    labels = {
      # 必要に応じてラベルを追加
      "managed-by" = "gcp-cloud-build-deploy-cloud-run"
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

