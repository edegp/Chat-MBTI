#!/usr/bin/env bash
# deploy/create-db-users.sh
# Generate unpredictable Cloud SQL users and store credentials in Secret Manager
set -euo pipefail
export LC_CTYPE=C

# Replace these with your GCP project and Cloud SQL instance names
PROJECT_ID="chat-mbti-458210"
INSTANCE_ID="mbti-diagnosis-api-postgres"

# Generate random suffix (8 hex chars)
RAND_SUFFIX() {
  openssl rand -hex 4
}

# Generate credentials
DB_APP_USER="app_$(RAND_SUFFIX)"
DB_APP_PASS=$(openssl rand -base64 32)
DB_ADMIN_USER="adm_$(RAND_SUFFIX)"
DB_ADMIN_PASS=$(openssl rand -base64 32)

# # Create or update users in Cloud SQL
# echo "Creating App user: $DB_APP_USER"
# gcloud sql users create "$DB_APP_USER" \
#   --instance="$INSTANCE_ID" \
#   --host="%" \
#   --project="$PROJECT_ID" \
#   --password="$DB_APP_PASS" || {
#     echo "Updating password for existing app user"
#     gcloud sql users set-password "$DB_APP_USER" \
#       --instance="$INSTANCE_ID" \
#       --host="%" \
#       --project="$PROJECT_ID" \
#       --password="$DB_APP_PASS"
# }

# echo "Creating Admin user: $DB_ADMIN_USER"
# gcloud sql users create "$DB_ADMIN_USER" \
#   --instance="$INSTANCE_ID" \
#   --host="%" \
#   --project="$PROJECT_ID" \
#   --password="$DB_ADMIN_PASS" || {
#     echo "Updating password for existing admin user"
#     gcloud sql users set-password "$DB_ADMIN_USER" \
#       --instance="$INSTANCE_ID" \
#       --host="%" \
#       --project="$PROJECT_ID" \
#       --password="$DB_ADMIN_PASS"
# }

# Store secrets in Secret Manager
echo "Storing credentials in Secret Manager"
# Helper function to create secret if not exists
ensure_secret() {
  local name=$1; shift
  local data=$1
  if ! gcloud secrets describe "$name" --project="$PROJECT_ID" &>/dev/null; then
    gcloud secrets create "$name" --project="$PROJECT_ID" --data-file=<(echo -n "$data")
  fi
  gcloud secrets versions add "$name" --data-file=<(echo -n "$data")
}

ensure_secret db-app-user  "$DB_APP_USER"
ensure_secret db-app-pass  "$DB_APP_PASS"
ensure_secret db-admin-user "$DB_ADMIN_USER"
ensure_secret db-admin-pass  "$DB_ADMIN_PASS"

echo "Done:"
echo "  DB_APP_USER=$DB_APP_USER"
echo "  DB_ADMIN_USER=$DB_ADMIN_USER"


# ユーザー作成後
printf "
GRANT CONNECT ON DATABASE mbti_diagnosis TO \"$DB_APP_USER\";
GRANT USAGE   ON SCHEMA public          TO \"$DB_APP_USER\";
GRANT SELECT, INSERT, UPDATE, DELETE
  ON ALL TABLES IN SCHEMA public       TO \"$DB_APP_USER\";
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO \"$DB_APP_USER\";
" | gcloud beta sql connect "$INSTANCE_ID" --user="$DB_ADMIN_USER" --database="mbti_diagnosis" --quiet
