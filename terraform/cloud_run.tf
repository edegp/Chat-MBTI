# Make the service publicly accessible
resource "google_cloud_run_v2_service_iam_member" "diagnosis_chat_public_access" {
  name     = var.diagnosis_chat.name
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
  bucket = var.diagnosis_chat.bucket_name
  role   = "roles/storage.legacyBucketWriter"
  member = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}



resource "google_cloud_run_v2_service" "main" {
  name     = var.diagnosis_chat.name
  location = var.region
  project  = var.project_id

  template {
    # Enable private VPC connectivity
    vpc_access {
      connector = "projects/${var.project_id}/locations/${var.region}/connectors/${var.diagnosis_chat.vpc.connector_name}"
      egress    = "ALL_TRAFFIC"
    }
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/${lower(var.diagnosis_chat.github.repo)}/${var.diagnosis_chat.name}:latest"
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
            secret  = "${var.app_name}-gemini-api-key"
            version = "latest"
          }
        }
      }
      env {
        name = "SQL_CONNECTION_NAME"
        value_source {
          secret_key_ref {
            secret  = "${var.diagnosis_chat.name}-cloudsql-connection-name"
            version = "latest"
          }
        }
      }
      env {
        name = "DB_APP_USER"
        value_source {
          secret_key_ref {
            secret  = "${var.diagnosis_chat.name}-db-app-user"
            version = "latest"
          }
        }
      }
      env {
        name = "DB_APP_PASS"
        value_source {
          secret_key_ref {
            secret  = "${var.diagnosis_chat.name}-db-app-pass"
            version = "latest"
          }
        }
      }
      env {
        name = "DB_ADMIN_USER"
        value_source {
          secret_key_ref {
            secret  = "${var.diagnosis_chat.name}-db-admin-user"
            version = "latest"
          }
        }
      }
      env {
        name = "DB_ADMIN_PASS"
        value_source {
          secret_key_ref {
            secret  = "${var.diagnosis_chat.name}-db-admin-pass"
            version = "latest"
          }
        }
      }

      # GCS bucket name for data uploads
      env {
        name  = "GCS_BUCKET_NAME"
        value = var.diagnosis_chat.bucket_name
      }
      resources {
        limits = {
          cpu    = var.diagnosis_chat.cpu_limit
          memory = var.diagnosis_chat.memory_limit
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
        instances = ["${var.project_id}:${var.region}:mbti-diagnosis-api-postgres"]
      }
    }
    annotations = {
      "autoscaling.knative.dev/maxScale"      = "100"
      "run.googleapis.com/startup-cpu-boost"  = "true"
      "run.googleapis.com/cloudsql-instances" = "${var.project_id}:${var.region}:mbti-diagnosis-api-postgres"
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

# create buket for GCS FUSE
resource "google_storage_bucket" "fuse_bucket" {
  name     = var.diagnosis_summary.fuse_bucket_name
  location = "ASIA-SOUTHEAST1"
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = true

  labels = {
    managed_by = "gcp-cloud-build-deploy-chat-api"
  }
}

################################
#  Cloud Run (Gen2) Service    #
################################

resource "google_cloud_run_v2_service" "service" {
  name = var.diagnosis_summary.name
  # gpu region
  location            = "asia-southeast1"
  project             = var.project_id
  provider            = google-beta
  deletion_protection = false

  template {
    service_account = google_service_account.cloud_run_sa.email
    # -------------------------
    #  Volume: GCS FUSE bucket
    # -------------------------
    volumes {
      name = "hf-cache"
      gcs {
        bucket    = var.diagnosis_summary.fuse_bucket_name
        read_only = false
      }
    }
    node_selector {
      accelerator = "nvidia-l4"
    }
    max_instance_request_concurrency = 1
    gpu_zonal_redundancy_disabled    = true
    # -------------------------
    #  Container definition
    # -------------------------
    containers {

      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/${lower(var.diagnosis_summary.github.repo)}/${var.diagnosis_summary.name}:latest"

      ports {
        name           = "http1"
        container_port = 10000
      }
      # Runtime environment variables so Transformers uses the mounted cache
      env {
        name  = "HF_HOME"
        value = "/workspace"
      }
      env {
        name  = "HF_HUB_OFFLINE"
        value = "1"
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "${var.app_name}-gemini-api-key"
            version = "latest"
          }
        }
      }

      # Mount the volume
      volume_mounts {
        name       = "hf-cache"
        mount_path = "/workspace"
      }

      # Resource limits (adjust)
      resources {
        limits = {
          memory           = var.diagnosis_summary.memory_limit
          cpu              = var.diagnosis_summary.cpu_limit
          "nvidia.com/gpu" = "1"
        }
        startup_cpu_boost = true
      }
    }
    # Autoscaling
    scaling {
      min_instance_count = var.diagnosis_summary.min_instances
      max_instance_count = var.diagnosis_summary.max_instances
    }
    timeout = "1200s"
    labels = {
      # 必要に応じてラベルを追加
      "managed-by" = "gcp-cloud-build-deploy-summary-api"
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}


resource "google_cloud_run_v2_service_iam_member" "diagnosis_summary_public_access" {
  name       = var.diagnosis_summary.name
  location   = "asia-southeast1"
  role       = "roles/run.invoker"
  member     = "allUsers"
  depends_on = [google_cloud_run_v2_service.service]
}
