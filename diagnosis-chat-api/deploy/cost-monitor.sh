#!/bin/bash

# Cost monitoring script for MBTI Diagnosis API
PROJECT_ID=${PROJECT_ID:-"chat-mbti-458210"}

echo "💰 MBTI診断API - 費用レポート"
echo "================================"
echo "プロジェクト: ${PROJECT_ID}"
echo "日時: $(date)"
echo ""

# Current month billing
echo "📊 今月の請求額:"
gcloud billing accounts list --format="table(displayName,billingAccountId)"
echo ""

# Cloud Run usage
echo "🏃 Cloud Run使用状況:"
gcloud run services list --region=asia-northeast1 --format="table(metadata.name,status.url,status.traffic[0].percent)"
echo ""

# Cloud SQL usage
echo "🗄️  Cloud SQL使用状況:"
gcloud sql instances list --format="table(name,databaseVersion,gceZone,settings.tier,state)"
echo ""

# Artifact Registry usage
echo "📦 Artifact Registry使用状況:"
gcloud artifacts repositories list --location=asia-northeast1 --format="table(name,format,createTime)"
echo ""

# Get billing data (requires billing API)
echo "💴 今月の概算費用 (Cloud Billing APIが有効な場合):"
# Note: This requires Cloud Billing API to be enabled and proper permissions
gcloud billing accounts get-iam-policy $(gcloud billing accounts list --format="value(billingAccountId)" --limit=1) 2>/dev/null || echo "請求情報にアクセスできません。Cloud Billing APIの有効化と権限設定が必要です。"

echo ""
echo "詳細な費用情報はGoogle Cloud Consoleの請求セクションで確認できます:"
echo "https://console.cloud.google.com/billing"
