# Terraform variables for MBTI Diagnosis API deployment
project_id = "chat-mbti-458210"

# Optional customizations
region = "asia-northeast1"
app_name = "mbti-diagnosis-api"
min_instances = 0
max_instances = 10
cpu_limit = "1"
memory_limit = "2Gi"
db_tier = "db-g1-small"
db_name = "mbti_diagnosis"
gemini_api_key = "AIzaSyDM58NqkGydvxHXum0PfrUCFg4W8JsM5m4"

github_owner = "edegp"  # 例: edegp
github_repo  = "Chat-MBTI"
ar_hostname = "asia-northeast1-docker.pkg.dev"
ar_repository = "cloud-run-source-deploy"
gcs_bucket_name= "mbti_qa_data_collection"
