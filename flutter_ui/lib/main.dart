import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_ui/firebase_options.dart';

import 'email_verification_page.dart';
import 'chat_page_friendly.dart';
import 'auth_guard.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'home.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

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
      initialRoute: "/",
      routes: {
        '/': (ctx) => const LoginPage(),
        '/chat': (ctx) => const AuthGuard(child: FriendlyChatPage()),
        // '/resetpassword': (ctx) => const ResetPasswordPage(),
      },
    );
  }
}
