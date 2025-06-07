# Chat-MBTI

AIを活用したMBTI性格診断チャットアプリケーション

## 🌟 概要

Chat-MBTIは、Google Gemini AIを使用してMBTI（Myers-Briggs Type Indicator）性格診断を行うWebアプリケーションです。ユーザーとの自然な会話を通じて性格を分析し、16種類のMBTIタイプを診断します。

## 🏗️ アーキテクチャ

### Backend (FastAPI + PostgreSQL)
- **API サーバー**: Google Cloud Run
- **データベース**: Cloud SQL (PostgreSQL)
- **AI モデル**: Google Gemini API
- **認証**: Firebase Authentication

### Frontend (Flutter Web)
- **ホスティング**: Firebase Hosting
- **認証**: Firebase Authentication
- **UI フレームワーク**: Flutter Web

## 🚀 本番環境URL

- **Webアプリ**: https://chat-mbti-458210.web.app
- **API サーバー**: https://chat-mbti-47665095629.asia-northeast1.run.app
- **API ドキュメント**: https://chat-mbti-47665095629.asia-northeast1.run.app/docs

## 📦 デプロイ方法

### 前提条件

1. **Google Cloud SDK** のインストール
```bash
# macOS
brew install google-cloud-sdk

# 認証
gcloud auth login
gcloud config set project chat-mbti-458210
```

2. **Firebase CLI** のインストール
```bash
npm install -g firebase-tools
firebase login
```

3. **Flutter SDK** のインストール
```bash
# macOS
brew install flutter
```

4. **Terraform** のインストール（インフラ管理用）
```bash
brew install terraform
```

### Backend API のデプロイ

#### 1. 環境変数の設定
```bash
cd diagnosis-ai-api
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars を編集して適切な値を設定
```

#### 2. Terraform でインフラをデプロイ
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

#### 3. Docker イメージのビルドとプッシュ
```bash
cd ..
# Docker イメージをビルド
docker build --platform linux/amd64 -t asia-northeast1-docker.pkg.dev/chat-mbti-458210/mbti-diagnosis-api-repo/mbti-diagnosis-api:latest .

# Artifact Registry に認証
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージをプッシュ
docker push asia-northeast1-docker.pkg.dev/chat-mbti-458210/mbti-diagnosis-api-repo/mbti-diagnosis-api:latest
```

#### 4. Cloud Run にデプロイ
```bash
# Terraform で自動デプロイ、または手動デプロイ
gcloud run deploy chat-mbti \
  --image asia-northeast1-docker.pkg.dev/chat-mbti-458210/mbti-diagnosis-api-repo/mbti-diagnosis-api:latest \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated
```

#### 5. Cloud Build による自動デプロイ（オプション）
```bash
# Cloud Build トリガーを設定
./setup-cloudbuild.sh
```

### Frontend (Flutter Web) のデプロイ

#### 1. 依存関係のインストール
```bash
cd flutter_ui
flutter pub get
```

#### 2. Webアプリのビルド
```bash
flutter build web --release
```

#### 3. Firebase Hosting にデプロイ
```bash
firebase deploy --only hosting
```

## 🔧 開発環境のセットアップ

### Backend 開発環境

```bash
cd diagnosis-ai-api

# Python環境のセットアップ（uvを使用）
brew install uv
uv sync

# PostgreSQLのインストール
brew install postgresql
brew services start postgresql

# データベースの作成
createdb chat_mbti

# 環境変数の設定
export DATABASE_URL="postgresql://username:password@localhost:5432/chat_mbti"
export GEMINI_API_KEY="your-gemini-api-key"

# アプリケーションの起動
uv run python app.py
```

### Frontend 開発環境

```bash
cd flutter_ui

# 依存関係のインストール
flutter pub get

# Webアプリの起動
flutter run -d chrome
```

## 🔄 継続的デプロイメント

### GitHub Actions（推奨）

`.github/workflows/deploy.yml` を作成：

```yaml
name: Deploy to Google Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy-api:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Google Cloud
      uses: google-github-actions/setup-gcloud@v0
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: chat-mbti-458210
    
    - name: Build and Deploy API
      run: |
        cd diagnosis-ai-api
        docker build --platform linux/amd64 -t asia-northeast1-docker.pkg.dev/chat-mbti-458210/mbti-diagnosis-api-repo/mbti-diagnosis-api:latest .
        docker push asia-northeast1-docker.pkg.dev/chat-mbti-458210/mbti-diagnosis-api-repo/mbti-diagnosis-api:latest
        gcloud run deploy chat-mbti --image asia-northeast1-docker.pkg.dev/chat-mbti-458210/mbti-diagnosis-api-repo/mbti-diagnosis-api:latest --region asia-northeast1

  deploy-web:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.7.2'
    
    - name: Build and Deploy Web
      run: |
        cd flutter_ui
        flutter pub get
        flutter build web --release
        npm install -g firebase-tools
        firebase deploy --only hosting --token ${{ secrets.FIREBASE_TOKEN }}
```

### Cloud Build

自動デプロイ用のCloud Buildトリガーが設定済み：

```bash
# トリガーの手動実行
cd diagnosis-ai-api
./setup-cloudbuild.sh
```

## 📊 監視・ログ

### ログの確認
```bash
# Cloud Run ログ
gcloud logs read "resource.type=cloud_run_revision" --limit 50

# Firebase Hosting ログ
firebase hosting:logs
```

### パフォーマンス監視
- Google Cloud Console でCloud Runのメトリクスを確認
- Firebase Console でHostingの使用状況を確認

## 🔐 セキュリティ設定

### 環境変数・シークレット管理
- Google Secret Manager を使用
- Firebase Authentication で認証
- HTTPS強制（自動設定済み）

### API キーの管理
```bash
# Secret Manager に保存
gcloud secrets create gemini-api-key --data-file=-
```

## 💰 コスト監視

```bash
# コスト監視スクリプトの実行
cd diagnosis-ai-api
./cost-monitor.sh
```

## 🐛 トラブルシューティング

### よくある問題

1. **Docker ビルドエラー**
```bash
# Dockerのリセット
docker system prune -a
```

2. **Firebase デプロイエラー**
```bash
# Firebase の再認証
firebase login --reauth
```

3. **Flutter ビルドエラー**
```bash
# Flutter のクリーンビルド
flutter clean
flutter pub get
flutter build web --release
```

## 📞 サポート

問題が発生した場合は、以下のリソースを参照してください：

- [API実装ドキュメント](diagnosis-ai-api/IMPLEMENTATION_COMPLETE.md)
- [Cloud Build設定ガイド](diagnosis-ai-api/CLOUDBUILD_SETUP.md)
- [Firebase Hostingガイド](flutter_ui/FIREBASE_HOSTING_SETUP.md)

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。