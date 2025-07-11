// File generated by FlutterFire CLI.
// ignore_for_file: type=lint
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Default [FirebaseOptions] for use with your Firebase apps.
///
/// Example:
/// ```dart
/// import 'firebase_options.dart';
/// // ...
/// await Firebase.initializeApp(
///   options: DefaultFirebaseOptions.currentPlatform,
/// );
/// ```
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return macos;
      case TargetPlatform.windows:
        return windows;
      case TargetPlatform.linux:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for linux - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'AIzaSyAYpGmS03x1MykjCpTbwgE9KuI88yX0AhE',
    appId: '1:47665095629:web:98965437707cb909d05a84',
    messagingSenderId: '47665095629',
    projectId: 'chat-mbti-458210',
    authDomain: 'chat-mbti-458210.firebaseapp.com',
    storageBucket: 'chat-mbti-458210.firebasestorage.app',
  );

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyBlWNOOorDqzSqXizA0SMIixyrURQKJpZg',
    appId: '1:47665095629:android:bb61ad38c2a78063d05a84',
    messagingSenderId: '47665095629',
    projectId: 'chat-mbti-458210',
    storageBucket: 'chat-mbti-458210.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyDsYBcvHjVarMnQpDZkcY8tk2ps1lLdAOY',
    appId: '1:47665095629:ios:b952d5de21082d32d05a84',
    messagingSenderId: '47665095629',
    projectId: 'chat-mbti-458210',
    storageBucket: 'chat-mbti-458210.firebasestorage.app',
    iosClientId: '47665095629-fvktdn96mblt00kc0j9527mk6uuu9ku3.apps.googleusercontent.com',
    iosBundleId: 'com.example.flutterUi',
  );

  static const FirebaseOptions macos = FirebaseOptions(
    apiKey: 'AIzaSyDsYBcvHjVarMnQpDZkcY8tk2ps1lLdAOY',
    appId: '1:47665095629:ios:b952d5de21082d32d05a84',
    messagingSenderId: '47665095629',
    projectId: 'chat-mbti-458210',
    storageBucket: 'chat-mbti-458210.firebasestorage.app',
    iosClientId: '47665095629-fvktdn96mblt00kc0j9527mk6uuu9ku3.apps.googleusercontent.com',
    iosBundleId: 'com.example.flutterUi',
  );

  static const FirebaseOptions windows = FirebaseOptions(
    apiKey: 'AIzaSyAYpGmS03x1MykjCpTbwgE9KuI88yX0AhE',
    appId: '1:47665095629:web:fc8c02bc4fc747cbd05a84',
    messagingSenderId: '47665095629',
    projectId: 'chat-mbti-458210',
    authDomain: 'chat-mbti-458210.firebaseapp.com',
    storageBucket: 'chat-mbti-458210.firebasestorage.app',
  );

}