# GitHub Actions CI/CD Setup

This repository includes a comprehensive GitHub Actions workflow that:

1. **Tests the Python API** using pytest with coverage reporting
2. **Tests and builds the Flutter app** with code analysis
3. **Deploys the Flutter app** to Firebase Hosting (main branch only)
4. **Comments on PRs** with test results and deployment status

## Prerequisites

### 1. Firebase Project Setup

- Firebase project: `chat-mbti-458210` (already configured)
- Firebase Hosting enabled
- Firebase CLI configured

### 2. Google Cloud Project Setup

- GCP project: `chat-mbti-458210` (already configured)
- Cloud Run service deployed
- Artifact Registry repository created

## Required GitHub Secrets

Add these secrets to your GitHub repository settings (`Settings` > `Secrets and variables` > `Actions`):

### Firebase Deployment Secrets

#### Option A: Using Firebase Token (Recommended)

```bash
# Login to Firebase and get CI token
firebase login:ci
```

Add the token as:

- **Secret Name:** `FIREBASE_TOKEN`
- **Secret Value:** `your-firebase-ci-token`

#### Option B: Using Service Account Key

Create a Firebase service account key and add:

- **Secret Name:** `FIREBASE_SERVICE_ACCOUNT_KEY`
- **Secret Value:** Base64-encoded service account JSON key

## Workflow Configuration

### Environment Variables

The workflow uses these environment variables (configured in the workflow file):

- `PROJECT_ID`: `chat-mbti-458210`
- `FLUTTER_VERSION`: `3.7.2`
- `PYTHON_VERSION`: `3.12`
- `NODE_VERSION`: `18`

### Triggers

The workflow runs on:

- **Push to main branch:** Full deployment pipeline
- **Push to develop branch:** Tests only
- **Pull requests to main:** Tests only with PR comments

### Jobs Overview

#### 1. `test-api`

- Sets up Python 3.12 and UV package manager
- Installs dependencies using `uv sync`
- Runs pytest with coverage reporting
- Uploads coverage to Codecov

#### 2. `test-flutter`

- Sets up Flutter 3.7.2
- Runs `flutter analyze` for code quality
- Runs `flutter test` for unit tests
- Builds Flutter web app
- Uploads build artifacts

#### 3. `deploy-firebase` (main branch only)

- Downloads Flutter build artifacts
- Configures Firebase Hosting
- Deploys to Firebase Hosting
- Creates optimized hosting configuration with caching

#### 4. `comment` (PR only)

- Comments on pull requests with test results
- Shows detailed status of API and Flutter tests
- Provides links to workflow runs and commit details

#### 5. `notify` (main branch only)

- Sends deployment status notifications
- Reports success/failure status

## Firebase Hosting Configuration

The workflow automatically creates an optimized `firebase.json` for hosting:

```json
{
  "hosting": {
    "public": "build/web",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|woff2)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

## Testing Locally

### API Tests

```bash
cd diagnosis-chat-api
uv run pytest --cov=src --cov-report=term-missing
```

### Flutter Tests

```bash
cd frontend
flutter test
flutter analyze
flutter build web
```

## Deployment URLs

After successful deployment:

- **Frontend:** `https://chat-mbti-458210.web.app`

## PR Comments

For pull requests, the workflow automatically comments with:

- ✅/❌ Test status for API and Flutter
- 📋 Links to workflow runs and commit details
- 🔍 Summary of test results

## Troubleshooting

### Common Issues

1. **Firebase Token Expired**

   - Re-run `firebase login:ci` and update the secret

2. **GCP Permissions Error**

   - Verify service account has correct IAM roles
   - Check that all required APIs are enabled

3. **Flutter Build Fails**

   - Check Flutter version compatibility
   - Verify all dependencies are properly configured

4. **API Tests Fail**
   - Check Python version and UV installation
   - Verify all test dependencies are included

### Debug Steps

1. **Check workflow logs** in GitHub Actions tab
2. **Verify secrets** are properly configured
3. **Test locally** before pushing to main
4. **Check Firebase/GCP console** for deployment status

## Security Notes

- All sensitive data (API keys, service account keys) are stored as GitHub secrets
- Firebase Hosting is configured with appropriate caching headers
- Cloud Run deployment uses managed service accounts
- Database credentials are managed through Google Secret Manager

## Cost Optimization

- **GitHub Actions:** 2,000 minutes/month free for public repos
- **Firebase Hosting:** 125GB storage + 10GB/month transfer free
- **Cloud Run:** Pay-per-use with automatic scaling to zero
- **Cloud Build:** 120 build-minutes/day free

---

For questions or issues, please check the workflow logs or create an issue in this repository.
