import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_ui/firebase_options.dart';
import 'package:url_strategy/url_strategy.dart';

import 'chat_page_friendly.dart';
import 'data_collection_page.dart';
import 'auth_guard.dart';
import 'package:flutter/material.dart';
import 'home.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Remove '#' from Flutter web URL
  setPathUrlStrategy();

  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
  } catch (e) {
    if (kDebugMode) {
      print('Failed to initialize Firebase: $e');
    }
  }

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MBTI-Chat',
      theme: ThemeData(
        fontFamily: 'NotoSansJP', // 日本語フォント推奨
        scaffoldBackgroundColor: const Color(0xFFFAF9F6), // クリーム色
      ),
      initialRoute: "/data-collection",
      routes: {
        '/': (ctx) => const LoginPage(),
        '/chat': (ctx) => const AuthGuard(child: FriendlyChatPage()),
        '/data-collection': (ctx) => const DataCollectionPage(),
        // '/resetpassword': (ctx) => const ResetPasswordPage(),
      },
    );
  }
}
