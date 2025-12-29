
# Service account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "${var.app_name}-cloud-run"
  display_name = "Cloud Run Service Account for ${var.app_name}"
}
#Grant necessary permissions to the service account
resource "google_project_iam_member" "cloud_run_sa_permissions" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/firebase.admin",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator"
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
  location = var.region
  name     = var.diagnosis_chat.name
  project  = var.project_id

  template {
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/${lower(var.diagnosis_chat.github.repo)}/${var.diagnosis_chat.name}:latest"
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
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "${var.app_name}-gemini-api-key"
            version = "latest"
          }
        }
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = "${var.diagnosis_chat.name}-database-url"
            version = "latest"
          }
        }
      }

      # GCS bucket name for data uploads
      env {
        name  = "GCS_BUCKET_NAME"
        value = var.diagnosis_chat.bucket_name
      }
      env {
        name  = "SUMMARY_API_URL"
        value = "https://mbti-diagnosis-summary-47665095629.asia-southeast1.run.app"
      }
      resources {
        limits = {
          cpu    = var.diagnosis_chat.cpu_limit
          memory = var.diagnosis_chat.memory_limit
        }
        startup_cpu_boost = true
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
    annotations = {
      "autoscaling.knative.dev/maxScale" = "100"
    }
    labels = {
      # 必要に応じてラベルを追加
      "managed-by" = "gcp-cloud-build-deploy-cloud-run"
    }
    timeout = "900s"
  }


  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}

# create buket for GCS FUSE
resource "google_storage_bucket" "fuse_bucket" {
  name     = var.diagnosis_summary.fuse_bucket_name
  location = var.region
  project  = var.project_id

  uniform_bucket_level_access = true
  force_destroy               = true

  labels = {
    managed_by = "gcp-cloud-build-deploy-chat-api"
  }
}

# Make the service publicly accessible
resource "google_cloud_run_v2_service_iam_member" "diagnosis_chat_public_access" {
  name       = var.diagnosis_chat.name
  location   = var.region
  role       = "roles/run.invoker"
  member     = "allUsers"
  depends_on = [google_cloud_run_v2_service.main]
}

################################
#  Cloud Run (Gen2) Service    #
################################
# resource "google_cloud_run_v2_service_iam_member" "diagnosis_summary_public_access" {
#   name     = google_cloud_run_v2_service.service.name
#   location = var.region
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }
resource "google_cloud_run_v2_service" "service" {
  name     = var.diagnosis_summary.name
  location = var.region
  project  = var.project_id
  provider = google-beta

  template {
    service_account = google_service_account.cloud_run_sa.email

    volumes {
      name = "hf-cache"
      gcs {
        bucket    = var.diagnosis_summary.fuse_bucket_name
        read_only = false
      }
    }
    # node_selector and gpu_zonal_redundancy_disabled are not supported in Cloud Run Gen2
    node_selector {
      accelerator = "nvidia-l4"
    }
    gpu_zonal_redundancy_disabled = true


    max_instance_request_concurrency = 10
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/${lower(var.diagnosis_summary.github.repo)}/${var.diagnosis_summary.name}:latest"
      ports {
        name           = "http1"
        container_port = 10000
      }
      env {
        name  = "HF_HOME"
        value = "/workspace"
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
      volume_mounts {
        name       = "hf-cache"
        mount_path = "/workspace"
      }
      resources {
        limits = {
          memory           = var.diagnosis_summary.memory_limit
          cpu              = var.diagnosis_summary.cpu_limit
          "nvidia.com/gpu" = "1"
        }
      }
    }
    scaling {
      min_instance_count = var.diagnosis_summary.min_instances
      max_instance_count = var.diagnosis_summary.max_instances
    }
    timeout = "900s"
    labels = {
      "managed-by" = "gcp-cloud-build-deploy-summary-api"
    }
    annotations = {
      "run.googleapis.com/ingress" = "all"
    }
  }
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}


resource "google_cloud_run_v2_service_iam_member" "diagnosis_summary_invoker" {
  name       = google_cloud_run_v2_service.service.name
  location   = var.region
  role       = "roles/run.invoker"
  member     = "serviceAccount:${google_service_account.cloud_run_sa.email}"
  depends_on = [google_cloud_run_v2_service.service]
}

resource "google_cloud_run_v2_service_iam_member" "diagnosis_summary_user_access" {
  name       = google_cloud_run_v2_service.service.name
  location   = var.region
  role       = "roles/run.invoker"
  member     = "user:a.yuhi1164@gmail.com"
  depends_on = [google_cloud_run_v2_service.service]
}
