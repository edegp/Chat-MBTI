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
    "roles/firebase.admin"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}


resource "google_cloud_run_v2_service" "main" {
  name     = var.app_name
  location = "asia-northeast1"
  project  = "chat-mbti-458210"

  template {
    containers {
      image = "asia-northeast1-docker.pkg.dev/chat-mbti-458210/cloud-run-source-deploy/chat-mbti/chat-mbti:latest"
      ports {
        name           = "http1"
        container_port = 8000
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = "chat-mbti-458210"
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
