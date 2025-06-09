# Cloud Build 自動デプロイセットアップガイド

このガイドでは、GitHub リポジトリから Cloud Build トリガーを使用して自動デプロイを設定する方法を説明します。

## 前提条件

1. Google Cloud プロジェクトが作成済み
2. GitHub リポジトリにコードがプッシュ済み
3. `gcloud` CLI がインストール・認証済み

## セットアップ手順

### 1. GitHub リポジトリ情報の設定

`terraform/terraform.tfvars` ファイルを編集して、GitHub リポジトリ情報を設定：

```hcl
# GitHub repository settings
github_owner = "your-actual-github-username"  # あなたのGitHubユーザー名
github_repo = "Chat-MBTI"                     # リポジトリ名
github_branch = "main"                        # デプロイ対象ブランチ
```

### 2. 手動で Cloud Build トリガーを作成（推奨）

```bash
# 環境変数を設定
export GITHUB_OWNER="your-actual-github-username"
export PROJECT_ID="chat-mbti-458210"

# セットアップスクリプトを実行
./setup-cloudbuild.sh
```

### 3. GitHub リポジトリとの接続

1. [Google Cloud Console - Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers) にアクセス
2. 作成されたトリガー `mbti-diagnosis-api-github-trigger` をクリック
3. 「Connect Repository」ボタンをクリック（まだ接続されていない場合）
4. GitHub OAuth フローに従ってリポジトリを接続

### 4. Terraform でインフラストラクチャを作成（オプション）

Terraform 経由でトリガーを管理したい場合：

```bash
cd terraform
terraform plan
terraform apply
```

## 自動デプロイの動作

設定完了後、以下の動作で自動デプロイが実行されます：

1. `main` ブランチ（設定したブランチ）にコードをプッシュ
2. Cloud Build トリガーが自動実行
3. Docker イメージがビルド（linux/amd64 プラットフォーム）
4. Artifact Registry にプッシュ
5. Cloud Run サービスが自動更新

## ビルド設定

`cloudbuild.yaml` ファイルで以下を設定済み：

- **プラットフォーム**: `linux/amd64` (Cloud Run 対応)
- **リソース**: E2_HIGHCPU_8 マシンタイプ
- **タイムアウト**: 20 分
- **ログ**: Cloud Logging

## トラブルシューティング

### ビルドが失敗する場合

1. **権限エラー**: Cloud Build サービスアカウントに必要な権限があることを確認
2. **プラットフォームエラー**: `--platform=linux/amd64` が設定されていることを確認
3. **Secret Manager**: データベース URL と Gemini API key が設定されていることを確認

### ログの確認

```bash
# 最新のビルドログを確認
gcloud builds log --limit=1
```

### トリガーの一覧表示

```bash
# Cloud Buildトリガーの一覧
gcloud builds triggers list
```

## セキュリティ

- データベースパスワードと Gemini API Key は Secret Manager で管理
- Cloud Build サービスアカウントは最小権限の原則で設定
- リポジトリ接続は OAuth 経由で安全に実行

## コスト最適化

- Cloud Build: 1 日 120 分まで無料
- 最小インスタンス数: 0（コールドスタート許可）
- 自動スケーリング: 最大 10 インスタンス

---

問題が発生した場合は、Cloud Build のログを確認するか、Issues でお知らせください。
