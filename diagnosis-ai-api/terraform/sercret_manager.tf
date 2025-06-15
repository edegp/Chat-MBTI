resource "google_secret_manager_secret" "cloudsql_connection_name" {
  secret_id = "cloudsql_connection_name"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gemini_api_key" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "${var.app_name}-gemini-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "cloudsql_connection_name" {
  secret      = google_secret_manager_secret.cloudsql_connection_name.id
  secret_data = google_sql_database_instance.postgres.connection_name
}

resource "google_secret_manager_secret" "db_app_user" {
  secret_id = "db-app-user"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "db_app_user" {
  secret      = google_secret_manager_secret.db_app_user.id
  secret_data = google_sql_user.app.name
}

resource "google_secret_manager_secret" "db_app_pass" {
  secret_id = "db-app-pass"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "db_app_pass" {
  secret      = google_secret_manager_secret.db_app_pass.id
  secret_data = random_password.db_app_pass.result
}
resource "google_secret_manager_secret" "db_admin_user" {
  secret_id = "db-admin-user"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "db_admin_user" {
  secret      = google_secret_manager_secret.db_admin_user.id
  secret_data = google_sql_user.admin.name
}

resource "google_secret_manager_secret" "db_admin_pass" {
  secret_id = "db-admin-pass"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret_version" "db_admin_pass" {
  secret      = google_secret_manager_secret.db_admin_pass.id
  secret_data = random_password.db_admin_pass.result
}
