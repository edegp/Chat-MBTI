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
│ │ │ ├── **pycache**
│ │ │ │ ├── **init**.cpython-312.pyc
│ │ │ │ ├── auth.cpython-312.pyc
│ │ │ │ ├── db.cpython-312.pyc
│ │ │ │ ├── env.cpython-312.pyc
│ │ │ │ ├── langgraph_driver.cpython-312.pyc
│ │ │ │ └── model.cpython-312.pyc
│ │ │ ├── auth.py
│ │ │ ├── db.py
│ │ │ ├── env.py
│ │ │ ├── langgraph_driver.py
│ │ │ └── model.py
│ │ ├── exceptions.py
│ │ ├── gateway
│ │ │ ├── **pycache**
│ │ │ │ ├── llm_gateway.cpython-312.pyc
│ │ │ │ ├── repository_gateway.cpython-312.pyc
│ │ │ │ └── workflow_gateway.cpython-312.pyc
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
│ │ ├── terraform.tfstate.1749284908.backup
│ │ ├── terraform.tfstate.backup
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
├── linux
│ ├── CMakeLists.txt
│ ├── flutter
│ │ ├── CMakeLists.txt
│ │ ├── ephemeral
│ │ ├── generated_plugin_registrant.cc
│ │ ├── generated_plugin_registrant.h
│ │ └── generated_plugins.cmake
│ └── runner
│ ├── CMakeLists.txt
│ ├── main.cc
│ ├── my_application.cc
│ └── my_application.h
├── macos
│ ├── Flutter
│ │ ├── Flutter-Debug.xcconfig
│ │ ├── Flutter-Release.xcconfig
│ │ ├── GeneratedPluginRegistrant.swift
│ │ └── ephemeral
│ │ ├── Flutter-Generated.xcconfig
│ │ └── flutter_export_environment.sh
│ ├── Runner
│ │ ├── AppDelegate.swift
│ │ ├── Assets.xcassets
│ │ │ └── AppIcon.appiconset
│ │ │ ├── Contents.json
│ │ │ ├── app_icon_1024.png
│ │ │ ├── app_icon_128.png
│ │ │ ├── app_icon_16.png
│ │ │ ├── app_icon_256.png
│ │ │ ├── app_icon_32.png
│ │ │ ├── app_icon_512.png
│ │ │ └── app_icon_64.png
│ │ ├── Base.lproj
│ │ │ └── MainMenu.xib
│ │ ├── Configs
│ │ │ ├── AppInfo.xcconfig
│ │ │ ├── Debug.xcconfig
│ │ │ ├── Release.xcconfig
│ │ │ └── Warnings.xcconfig
│ │ ├── DebugProfile.entitlements
│ │ ├── GoogleService-Info.plist
│ │ ├── Info.plist
│ │ ├── MainFlutterWindow.swift
│ │ └── Release.entitlements
│ ├── Runner.xcodeproj
│ │ ├── project.pbxproj
│ │ ├── project.xcworkspace
│ │ │ └── xcshareddata
│ │ │ └── IDEWorkspaceChecks.plist
│ │ └── xcshareddata
│ │ └── xcschemes
│ │ └── Runner.xcscheme
│ ├── Runner.xcworkspace
│ │ ├── contents.xcworkspacedata
│ │ └── xcshareddata
│ │ └── IDEWorkspaceChecks.plist
│ └── RunnerTests
│ └── RunnerTests.swift
├── public
├── pubspec.lock
├── pubspec.yaml
├── test
│ └── widget_test.dart
├── web
│ ├── favicon.png
│ ├── icons
│ │ ├── Icon-192.png
│ │ ├── Icon-512.png
│ │ ├── Icon-maskable-192.png
│ │ └── Icon-maskable-512.png
│ ├── index.html
│ └── manifest.json
└── windows
├── CMakeLists.txt
├── flutter
│ ├── CMakeLists.txt
│ ├── ephemeral
│ ├── generated_plugin_registrant.cc
│ ├── generated_plugin_registrant.h
│ └── generated_plugins.cmake
└── runner
├── CMakeLists.txt
├── Runner.rc
├── flutter_window.cpp
├── flutter_window.h
├── main.cpp
├── resource.h
├── resources
│ └── app_icon.ico
├── runner.exe.manifest
├── utils.cpp
├── utils.h
├── win32_window.cpp
└── win32_window.h
