import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class EmailVerificationPage extends StatefulWidget {
  final String email;

  const EmailVerificationPage({Key? key, required this.email})
    : super(key: key);

  @override
  State<EmailVerificationPage> createState() => _EmailVerificationPageState();
}

class _EmailVerificationPageState extends State<EmailVerificationPage> {
  final List<TextEditingController> _controllers = List.generate(
    6,
    (index) => TextEditingController(),
  );
  final List<FocusNode> _focusNodes = List.generate(6, (index) => FocusNode());

  @override
  void dispose() {
    for (var controller in _controllers) {
      controller.dispose();
    }
    for (var node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32.0),
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
              mainAxisSize: MainAxisSize.min,
              children: [
                // Email sent confirmation icon
                const Icon(
                  Icons.mark_email_read,
                  size: 64,
                  color: Colors.green,
                ),
                const SizedBox(height: 24),

                // Title
                const Text(
                  'メールを送信しました',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),

                // Email address
                Text(
                  widget.email,
                  style: const TextStyle(fontSize: 16, color: Colors.black54),
                ),
                const SizedBox(height: 24),

                // Instruction text
                const Text(
                  'メールに記載された6桁の認証コードを入力してください',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 32),

                // Verification code input fields
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: List.generate(
                    6,
                    (index) => SizedBox(
                      width: 45,
                      child: TextField(
                        controller: _controllers[index],
                        focusNode: _focusNodes[index],
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 20),
                        keyboardType: TextInputType.number,
                        inputFormatters: [
                          LengthLimitingTextInputFormatter(1),
                          FilteringTextInputFormatter.digitsOnly,
                        ],
                        decoration: InputDecoration(
                          contentPadding: EdgeInsets.zero,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(color: Colors.grey),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                            borderSide: const BorderSide(
                              color: Colors.black,
                              width: 2,
                            ),
                          ),
                        ),
                        onChanged: (value) {
                          if (value.isNotEmpty) {
                            // Move to next field
                            if (index < 5) {
                              _focusNodes[index + 1].requestFocus();
                            } else {
                              // Submit code when all filled
                              _focusNodes[index].unfocus();
                              _verifyCode();
                            }
                          } else if (index > 0) {
                            // Move to previous field on delete
                            _focusNodes[index - 1].requestFocus();
                          }
                        },
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 32),

                // Verify button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _verifyCode,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: const Text(
                      '認証する',
                      style: TextStyle(fontSize: 16, color: Colors.white),
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Resend code option
                TextButton(
                  onPressed: () {
                    // Add code to resend verification email
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('認証コードを再送信しました'),
                        duration: Duration(seconds: 2),
                      ),
                    );
                  },
                  child: const Text(
                    'コードを再送信する',
                    style: TextStyle(
                      color: Colors.black54,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _verifyCode() {
    // Combine all codes
    String verificationCode = _controllers.map((c) => c.text).join();

    // Check if all fields are filled
    if (verificationCode.length != 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('6桁の認証コードを入力してください'),
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }

    // Add verification logic here
    print('Verification code: $verificationCode');

    // Navigate to next screen or show success message
    // For now, just show a snackbar
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('認証が完了しました'),
        duration: Duration(seconds: 2),
      ),
    );
  }
}
