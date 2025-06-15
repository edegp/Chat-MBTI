resource "google_secret_manager_secret" "cloudsql_connection_name" {
  secret_id = "cloudsql_connection_name"
    replication {
        auto {}
    }
}

resource "google_secret_manager_secret_version" "cloudsql_connection_name" {
  secret      = google_secret_manager_secret.cloudsql_connection_name.id
  secret_data = google_sql_database_instance.postgres.connection_name
}
