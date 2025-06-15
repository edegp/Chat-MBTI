## python package manager

uv

if you want to use pytest

```bash
uv run pytest ...
```

## Project Structure

.
├── FLUTTER_WEB_BUILD_FIXED.md
├── LICENSE
├── README.md
├── UI_HISTORY_RESTORE_IMPROVEMENT.md
├── diagnosis-ai-api
│ ├── Dockerfile
│ ├── README.md
│ ├── config
│ │ └── element.yaml
│ ├── coverage.xml
│ ├── deploy
│ │ ├── cost-monitor.sh
│ │ ├── deploy.sh
│ │ └── setup-cloudbuild.sh
│ ├── docker-compose.yaml
│ ├── docs
│ │ ├── CLOUDBUILD_SETUP.md
│ │ ├── ERROR_HANDLING_IMPLEMENTATION_COMPLETE.md
│ │ ├── IMPLEMENTATION_COMPLETE.md
│ │ ├── NEW_ARCHITECTURE_README.md
│ │ ├── architecture_proposal.md
│ │ ├── langgraph_architecture_redesign.md
│ │ └── エラーハンドリングレビューレポート.md
│ ├── firebase-adminsdk.json
│ ├── notebook
│ │ └── chatbot_v0.ipynb
│ ├── pyproject.toml
│ ├── src
│ │ ├── **init**.py
│ │ ├── api
│ │ │ ├── app.py
│ │ │ └── router.py
│ │ ├── controller
│ │ │ ├── **init**.py
│ │ │ ├── mbti_controller.py
│ │ │ └── type.py
│ │ ├── di_container.py
│ │ ├── driver
│ │ │ ├── **init**.py
│ │ │ ├── auth.py
│ │ │ ├── db.py
│ │ │ ├── env.py
│ │ │ ├── langgraph_driver.py
│ │ │ └── model.py
│ │ ├── exceptions.py
│ │ ├── gateway
│ │ │ ├── llm_gateway.py
│ │ │ ├── repository_gateway.py
│ │ │ └── workflow_gateway.py
│ │ ├── port
│ │ │ ├── **init**.py
│ │ │ └── ports.py
│ │ └── usecase
│ │ ├── **init**.py
│ │ ├── mbti_conversation_service.py
│ │ ├── prompt.py
│ │ ├── type.py
│ │ └── utils.py
│ ├── terraform
│ │ ├── README.md
│ │ ├── billing-alerts.tf
│ │ ├── cloudbuild.tf
│ │ ├── cloudbuild_simple.tf
│ │ ├── main.tf
│ │ ├── outputs.tf
│ │ ├── terraform.tfstate
│ │ ├── terraform.tfvars
│ │ ├── terraform.tfvars.example
│ │ └── variables.tf
│ ├── tests
│ │ ├── conftest.py
│ │ ├── test_api_error_handling.py
│ │ ├── test_controller_error_handling.py
│ │ ├── test_db.py
│ │ ├── test_error_handling.py
│ │ ├── test_error_handling_integration.py
│ │ ├── test_integration.py
│ │ ├── test_langgraph_driver.py
│ │ ├── test_mbti_controller.py
│ │ ├── test_mbti_conversation_service.py
│ │ ├── test_utils.py
│ │ └── test_workflow_gateway.py
│ └── uv.lock
└── flutter_ui
├── FIREBASE_HOSTING_SETUP.md
├── README.md
├── analysis_options.yaml
├── android
│ ├── app
├── assets
│ ├── fonts
├── lib
│ ├── auth_guard.dart
│ ├── chat_page_friendly.dart
│ ├── email_verification_page.dart
│ ├── firebase_options.dart
│ ├── home.dart
│ ├── main.dart
│ └── services
│ └── api_service.dart
├── pubspec.lock
├── pubspec.yaml
├── test
│ └── widget_test.dart

## Overall Project Specifications

- Backend (diagnosis-ai-api):

  - FastAPI with Clean Architecture: `api`, `controller`, `usecase`, `gateway`, `driver` modules
  - Dependency injection via `di_container.py` and Pydantic for request/response models
  - API endpoints for MBTI conversation: `/conversation/start`, `/conversation/answer`, `/conversation/complete`, and `/upload`
  - Error handling and logging, GCS upload integration, Terraform-based infrastructure, Cloud Build deployment
  - Test suite with pytest covering controllers, gateways, services, and integration tests

- Flutter UI (flutter_ui):

  - Flutter application with Firebase Auth guard, email verification, and chat interface (`chat_page_friendly.dart`)
  - HTTP integration via `DataCollectionApiService`, local state persisted with `SharedPreferences`
  - Japanese localization support with `NotoSansJP` font and UI themes
  - Pages: `auth_guard.dart`, `home.dart`, `main.dart`, `email_verification_page.dart`, and MBTI data collection flow
  - Widget tests under `test/widget_test.dart`

- CI/CD and Infrastructure:
  - Docker and `docker-compose` for local development (`diagnosis-ai-api`)
  - Terraform configurations under `diagnosis-ai-api/terraform` and Cloud Build scripts under `diagnosis-ai-api/deploy`
  - Python managed by `uv`, run backend tests with `uv run pytest ...`

## MBTI Data Collection Feature Summary

- Flutter UI:

  - 4 要素 ×10 問 ×5 サイクル（全 20 フェーズ）の MBTI 質問応答データ収集
  - 10 問ごとに SharedPreferences へ自動保存・復元
  - フェーズ単位／全体の CSV 出力ボタン実装
  - 16 性格コード入力フォーム追加、CSV ヘッダ＆行に反映
  - GCS アップロード機能：participant_name と personality_code 付きで安全に送信
  - 日本語フォント（NotoSansJP）対応
  - フェーズ内／跨ぎの「戻る」ナビゲーション
  - AppBar タップでリセット（確認ダイアログ表示）

- Backend (FastAPI):
  - リクエストモデルに personality_code を追加
  - コントローラとサービスで personality*code を受け取り、保存ディレクトリを mbti_data/{participant}*{code}に変更
  - `data-collection/upload`エンドポイントで CSV 受信＆GCS アップロード処理
  - pytest テストの更新が必要（personality_code 対応）
