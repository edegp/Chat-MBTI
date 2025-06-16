# Create database
resource "google_sql_database" "database" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "random_password" "db_app_pass" {
  length  = 32
  special = true
}

resource "random_password" "db_admin_pass" {
  length  = 32
  special = true
}

resource "random_id" "app" {
  byte_length = 6
}

resource "random_id" "admin" {
  byte_length = 6
}

resource "google_sql_user" "app" {
  name     = "app_${random_id.app.hex}"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_app_pass.result
}

resource "google_sql_user" "admin" {
  name     = "adm_${random_id.admin.hex}"
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_admin_pass.result
}

# Create Cloud SQL PostgreSQL instance for LangGraph checkpoints
resource "google_sql_database_instance" "postgres" {
  name             = "${var.app_name}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier                        = var.db_tier
    availability_type           = "ZONAL"
    disk_type                   = "PD_SSD"
    disk_size                   = 20
    disk_autoresize             = true
    disk_autoresize_limit       = 100
    deletion_protection_enabled = true
    ip_configuration {
      ipv4_enabled = true
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }
  }

  deletion_protection = false
  depends_on          = [google_project_service.required_apis]
}

