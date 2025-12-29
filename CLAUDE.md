# Chat-MBTI Project

MBTI性格診断チャットアプリケーション

## Architecture

```
Frontend (Flutter Web) -> diagnosis-chat-api (FastAPI) -> diagnosis-summary-api (FastAPI + ML)
                                    |
                                    v
                              Supabase (PostgreSQL)
```

## Services

### diagnosis-chat-api
- FastAPI + LangGraph
- Gemini API (gemini-3-flash-preview)
- Port: 8080
- Cloud Run: `mbti-diagnosis-api`

### diagnosis-summary-api
- FastAPI + Transformers
- ML models for MBTI classification
- Port: 8081
- Cloud Run: `mbti-diagnosis-summary`

### Frontend
- Flutter Web
- Firebase Hosting

## Infrastructure (GCP)

- **Region**: asia-southeast1
- **Database**: Supabase PostgreSQL (aws-1-ap-northeast-1)
- **Secrets**: Secret Manager
  - `chat-mbti-gemini-api-key`
  - `mbti-diagnosis-api-database-url`
- **CI/CD**: Cloud Build triggers (GitHub)
- **Container Registry**: Artifact Registry

## Local Development

```bash
# Backend
cd diagnosis-chat-api
uv sync
uv run uvicorn src.main:app --reload

# Frontend
cd frontend
flutter run -d chrome
```

## Environment Variables

### diagnosis-chat-api
- `GEMINI_API_KEY` - Gemini API key
- `DATABASE_URL` - Supabase connection string
- `GCS_BUCKET_NAME` - Storage bucket
- `SUMMARY_API_URL` - Summary API endpoint

### diagnosis-summary-api
- `GEMINI_API_KEY` - Gemini API key
- `HF_HOME` - Hugging Face cache directory

## Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Notes

- VPC Access Connector removed (cost optimization)
- Cloud SQL migrated to Supabase (cost optimization)
- API keys must not have trailing newlines in Secret Manager
