import 'package:shared_preferences/shared_preferences.dart';

import 'email_verification_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:firebase_auth/firebase_auth.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final TextEditingController emailController = TextEditingController();
  final _auth = FirebaseAuth.instance;
  final _email = TextEditingController();
  final _password = TextEditingController();
  String? _error;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    // Check if user is already logged in
    _checkCurrentUser();
    // Check if the app was opened with a sign-in link
    _checkForSignInLink();
  }

  // Check if user is already logged in
  void _checkCurrentUser() {
    final user = _auth.currentUser;
    if (user != null) {
      // User is already logged in, redirect to chat
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Navigator.pushReplacementNamed(context, '/chat');
      });
    }
  }

  @override
  void dispose() {
    emailController.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  // Check if app was opened with a sign-in link
  Future<void> _checkForSignInLink() async {
    // Get the link that launched the app
    final incomingLink = Uri.base.toString();
    if (_auth.isSignInWithEmailLink(incomingLink)) {
      try {
        // Get email from SharedPreferences
        final prefs = await SharedPreferences.getInstance();
        final email = prefs.getString('emailForSignIn');

        if (email == null) {
          // If email is not found, prompt user to enter their email
          // This could happen if they open the link on a different device
          // You could show a dialog here to ask for email
          return;
        }

        // Complete sign-in process
        await _auth.signInWithEmailLink(email: email, emailLink: incomingLink);

        // Clear stored email
        await prefs.remove('emailForSignIn');

        // Navigate to chat page
        if (mounted) {
          Navigator.pushReplacementNamed(context, '/chat');
        }
      } catch (e) {
        setState(() {
          _error = e.toString();
          _isProcessing = false;
        });
      }
    }
  }

  // Send sign-in link to email
  Future<void> _sendSignInLinkToEmail() async {
    final email = emailController.text.trim();
    if (email.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('メールアドレスを入力してください'),
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }

    setState(() {
      _isProcessing = true;
      _error = null;
    });

    try {
      // Save email to SharedPreferences to use later when sign-in link is clicked
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('emailForSignIn', email);

      // Configure ActionCodeSettings
      final actionCodeSettings = ActionCodeSettings(
        url: 'http://localhost:5000/', // Change to your app's domain
        handleCodeInApp: true,
        androidPackageName: 'flutter_ui (android)',
        androidInstallApp: true,
        // androidMinimumVersion: '12',
        iOSBundleId: 'com.example.flutterUi',
      );

      // Send sign-in link
      await _auth.sendSignInLinkToEmail(
        email: email,
        actionCodeSettings: actionCodeSettings,
      );

      // Show success message
      if (mounted) {
        // Navigate to email sent confirmation page
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => EmailVerificationPage(email: email),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => EmailVerificationPage(email: email),
          ),
        );
        setState(() {
          _error = e.toString();
          _isProcessing = false;
        });
      }
    }
  }

  // Google サインイン
  Future<void> _signInWithGoogle() async {
    try {
      final provider = GoogleAuthProvider()..addScope('email');
      await _auth.signInWithPopup(provider);

      final user = FirebaseAuth.instance.currentUser;
      if (user != null) {
        final idToken = await user.getIdToken(true);
        debugPrint(idToken);
      }

      if (mounted) {
        Navigator.pushReplacementNamed(context, '/chat');
      }
    } on FirebaseAuthException catch (e) {
      setState(() => _error = e.message);
    }
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
                      fontSize: 36,
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
                  fontSize: 42,
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
                style: TextStyle(fontSize: 18, color: Colors.black54),
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
                        child: GoogleSignInButton(onPressed: _signInWithGoogle),
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
                      // Error display
                      if (_error != null)
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.red.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.red.withValues(alpha: 0.3)),
                          ),
                          child: Text(
                            _error!,
                            style: const TextStyle(color: Colors.red, fontSize: 14),
                          ),
                        ),
                      if (_error != null) const SizedBox(height: 16),
                      // メールで続ける
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed:
                              _isProcessing ? null : _sendSignInLinkToEmail,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.black,
                            padding: const EdgeInsets.symmetric(vertical: 18),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child:
                              _isProcessing
                                  ? const SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                      color: Colors.white,
                                      strokeWidth: 2.0,
                                    ),
                                  )
                                  : const Text(
                                    'メールで続ける',
                                    style: TextStyle(
                                      fontSize: 18,
                                      color: Colors.white,
                                    ),
                                  ),
                        ),
                      ),
                      const SizedBox(height: 12),
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

// Googleログインボタンのウィジェット
class GoogleSignInButton extends StatefulWidget {
  final void Function()? onPressed;

  const GoogleSignInButton({super.key, this.onPressed});

  @override
  State<GoogleSignInButton> createState() => _GoogleSignInButtonState();
}

class _GoogleSignInButtonState extends State<GoogleSignInButton> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 40,
      child: OutlinedButton(
        onPressed: widget.onPressed,
        onHover: (value) {
          setState(() {
            _isHovered = value;
          });
        },
        style: OutlinedButton.styleFrom(
          backgroundColor: Colors.white,
          side: BorderSide(
            color: Color(0xFF747775).withValues(alpha: _isHovered ? 0.8 : 1.0),
          ),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(horizontal: 12),
          elevation: 0,
        ),
        child: Opacity(
          opacity: _isHovered ? 0.8 : 1.0,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
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
                height: 18.0,
                width: 18.0,
              ),
              const SizedBox(width: 8),
              // テキスト
              const Text(
                'Googleで続ける',
                style: TextStyle(
                  color: Color(0xFF1F1F1F),
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
