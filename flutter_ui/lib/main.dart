import 'email_verification_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Claude Login',
      theme: ThemeData(
        fontFamily: 'NotoSansJP', // 日本語フォント推奨
        scaffoldBackgroundColor: const Color(0xFFFAF9F6), // クリーム色
      ),
      home: const ClaudeLoginPage(),
    );
  }
}

// ... 省略（他のコードはそのまま） ...

// Googleログインボタンのウィジェット
Widget googleSignInButton({void Function()? onPressed}) {
  return SizedBox(
    width: double.infinity,
    height: 40,
    child: OutlinedButton(
      onPressed: onPressed,
      style: OutlinedButton.styleFrom(
        backgroundColor: Colors.white,
        side: const BorderSide(color: Color(0xFF747775)),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
        padding: const EdgeInsets.symmetric(horizontal: 12),
        elevation: 0,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          // Googleアイコン（SVG）
          SvgPicture.string(
            '''
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
              <path fill="none" d="M0 0h48v48H0z"/>
            </svg>
            ''',
            height: 20,
            width: 20,
          ),
          const SizedBox(width: 12),
          const Text(
            'Sign in with Google',
            style: TextStyle(
              color: Color(0xFF1f1f1f),
              fontSize: 14,
              fontFamily: 'Roboto',
              letterSpacing: 0.25,
              fontWeight: FontWeight.normal,
            ),
          ),
        ],
      ),
    ),
  );
}

class ClaudeLoginPage extends StatefulWidget {
  const ClaudeLoginPage({super.key});

  @override
  State<ClaudeLoginPage> createState() => _ClaudeLoginPageState();
}

class _ClaudeLoginPageState extends State<ClaudeLoginPage> {
  final TextEditingController emailController = TextEditingController();

  @override
  void dispose() {
    emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          child: Column(
            children: [
              const SizedBox(height: 48),
              // ロゴとサービス名
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Image.asset(
                    'assets/logo.png', // ロゴ画像を用意
                    height: 36,
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Chat-MBTI',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'serif',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 48),
              // キャッチコピー
              const Text(
                'あなたの本当の性格をお教えします',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.w500,
                  height: 1.2,
                  fontFamily: 'serif',
                ),
              ),
              const SizedBox(height: 16),
              // サブキャッチ
              const Text(
                '性格に基づいた相談で、自分が気づかなかった本当の自分を理解できる相談エージェント',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 16, color: Colors.black54),
              ),
              const SizedBox(height: 40),
              // カード
              Center(
                child: Container(
                  width: 400,
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black12,
                        blurRadius: 24,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      // Googleで続ける
                      SizedBox(
                        width: double.infinity,
                        child: googleSignInButton(onPressed: () {}),
                      ),
                      const SizedBox(height: 16),
                      // または
                      Row(
                        children: [
                          const Expanded(child: Divider()),
                          const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 8),
                            child: Text('または'),
                          ),
                          const Expanded(child: Divider()),
                        ],
                      ),
                      const SizedBox(height: 16),
                      // メールアドレス
                      TextField(
                        controller: emailController,
                        decoration: InputDecoration(
                          hintText: 'メールアドレスを入力してください',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          contentPadding: const EdgeInsets.symmetric(
                            vertical: 14,
                            horizontal: 16,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      // メールで続ける
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () {
                            // Get email from TextField (you'll need to add a controller)
                            String email = emailController.text;
                            if (email.isEmpty) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('メールアドレスを入力してください'),
                                  duration: Duration(seconds: 2),
                                ),
                              );
                              return;
                            }

                            // Navigate to verification page
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder:
                                    (context) =>
                                        EmailVerificationPage(email: email),
                              ),
                            );
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.black,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: const Text(
                            'メールで続ける',
                            style: TextStyle(fontSize: 16, color: Colors.white),
                          ),
                        ),
                      ),
                      // 利用規約
                      const Text.rich(
                        TextSpan(
                          style: TextStyle(fontFamily: 'Murecho'),
                          children: [
                            TextSpan(
                              text: '続行することにより、Chat-MBTIの',
                              style: TextStyle(fontSize: 12),
                            ),
                            TextSpan(
                              text: '利用規約',
                              style: TextStyle(
                                fontSize: 12,
                                decoration: TextDecoration.underline,
                                fontFamily: "Murecho",
                              ),
                            ),
                            TextSpan(
                              text: 'および',
                              style: TextStyle(fontSize: 12),
                            ),
                            TextSpan(
                              text: '利用ポリシー',
                              style: TextStyle(
                                fontSize: 12,
                                decoration: TextDecoration.underline,
                              ),
                            ),
                            TextSpan(
                              text: 'に同意し、',
                              style: TextStyle(fontSize: 12),
                            ),
                            TextSpan(
                              text: 'プライバシーポリシー',
                              style: TextStyle(
                                fontSize: 12,
                                decoration: TextDecoration.underline,
                              ),
                            ),
                            TextSpan(
                              text: 'を確認したものとみなされます。',
                              style: TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
