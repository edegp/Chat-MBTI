# Firebase Hosting & Flutter Web デプロイガイド

## 概要
Chat-MBTI Flutter UIアプリをFirebase Hostingにデプロイするための手順書です。

## 前提条件
- Firebase CLI がインストールされていること
- Google Cloud プロジェクト `chat-mbti-458210` へのアクセス権限
- Flutter SDK がインストールされていること

## デプロイ手順

### 1. Firebase CLI のインストール（未インストールの場合）
```bash
npm install -g firebase-tools
```

### 2. Firebase にログイン
```bash
firebase login
```

### 3. Flutter Web アプリをビルド
```bash
cd /Users/yuhiaoki/dev/Chat-MBTI/flutter_ui
flutter build web --release
```

### 4. Firebase Hosting にデプロイ
```bash
firebase deploy --only hosting
```

## カスタムドメイン（オプション）
Firebase Hostingは無料のドメインを提供しますが、カスタムドメインも設定可能です：

1. Firebase Console → Hosting → ドメインを追加
2. DNS設定でCNAMEレコードを追加
3. SSL証明書は自動的に設定されます

## 環境変数・設定
Flutter WebアプリはFirebase Authenticationを使用しているため、以下が自動的に設定されます：
- プロジェクトID: `chat-mbti-458210`
- Firebase Authentication設定
- Web用Firebase設定

## GitHub Actions（オプション）
継続的デプロイメントを設定する場合：

```yaml
name: Deploy to Firebase Hosting
on:
  push:
    branches: [ main ]
    paths: [ 'flutter_ui/**' ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.7.2'
    - run: flutter pub get
      working-directory: flutter_ui
    - run: flutter build web --release
      working-directory: flutter_ui
    - uses: FirebaseExtended/action-hosting-deploy@v0.7-alpha
      with:
        repoToken: '${{ secrets.GITHUB_TOKEN }}'
        firebaseServiceAccount: '${{ secrets.FIREBASE_SERVICE_ACCOUNT }}'
        projectId: chat-mbti-458210
        entryPoint: flutter_ui
```

## デプロイ後のURL
デプロイ完了後、以下のURLでアクセス可能になります：
- Default: `https://chat-mbti-458210.web.app`
- Alternative: `https://chat-mbti-458210.firebaseapp.com`

## トラブルシューティング

### ビルドエラーの場合
```bash
flutter clean
flutter pub get
flutter build web --release
```

### Firebase認証エラーの場合
```bash
firebase login --reauth
```

### プロジェクト設定確認
```bash
firebase projects:list
firebase use chat-mbti-458210
```

## セキュリティ設定
Firebase Hostingでは以下のセキュリティ機能が利用可能：
- HTTPS強制（デフォルト有効）
- CORS設定
- セキュリティヘッダー設定

## パフォーマンス最適化
- Flutter Webアプリの軽量化
- キャッシュ設定の最適化
- CDN配信（Firebase Hostingは全世界のCDNを使用）

## 監視・分析
Firebase Hostingでは以下の機能が利用可能：
- アクセス統計
- パフォーマンス監視
- エラートラッキング
