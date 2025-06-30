import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:frontend/firebase_options.dart';
import 'package:url_strategy/url_strategy.dart';
import 'dart:async';

import 'chat_page_friendly.dart';
import 'data_collection_page.dart';
import 'auth_guard.dart';
import 'package:flutter/material.dart';
import 'home.dart';
import 'result.dart';
import 'services/api_service.dart';

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
      title: 'Chat-MBTI',
      theme: ThemeData(
        fontFamily: 'NotoSansJP', // 日本語フォント推奨
        scaffoldBackgroundColor: const Color(0xFFFAF9F6), // クリーム色
      ),
      initialRoute: "/data-collection",
      debugShowCheckedModeBanner: false,
      // onGenerateRouteは不要
      routes: {
        '/': (ctx) => const LoginPage(),
        '/chat': (ctx) => const AuthGuard(child: FriendlyChatPage()),
        '/data-collection': (ctx) => const DataCollectionPage(),
        // '/resetpassword': (ctx) => const ResetPasswordPage(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/result') {
          final args = settings.arguments as Map<String, dynamic>?;
          final reportsRaw = args?['reports'] ?? [];
          final reports = reportsRaw is List<JudgeAndReport>
              ? reportsRaw
              : (reportsRaw is List
                  ? reportsRaw.map((e) => e is JudgeAndReport ? e : JudgeAndReport.fromJson(e as Map<String, dynamic>)).toList()
                  : <JudgeAndReport>[]);
          final reportFutures = args?['reportFutures'] as List<Future<JudgeAndReport>>? ?? [];
          final onReset = args?['onReset'] as VoidCallback?;
          return MaterialPageRoute(
            builder: (context) => AuthGuard(
              child: ResultPage(reports: reports, reportFutures: reportFutures, onRestartDiagnosis: onReset), // onResetを渡す
            ),
          );
        }
        return null; // ルートが見つからない場合はnullを返す
      },
    );
  }
}
