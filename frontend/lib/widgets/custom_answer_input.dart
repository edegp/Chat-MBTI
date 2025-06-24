import 'package:flutter/material.dart';

class CustomAnswerInput extends StatelessWidget {
  final TextEditingController textController;
  final Function(String) onAnswerSubmitted;

  const CustomAnswerInput({
    super.key,
    required this.textController,
    required this.onAnswerSubmitted,
  });

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isVerySmallScreen = screenWidth < 360;
    final isSmallScreen = screenWidth < 600;
    
    return Container(
      padding: EdgeInsets.all(
        isVerySmallScreen ? 12 : (isSmallScreen ? 16 : 20)
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(
          top: BorderSide(color: Colors.grey[200]!),
        ),
      ),
      child: Row(
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  child: TextField(
                    controller: textController,
                    style: TextStyle(
                      fontSize: isVerySmallScreen ? 14 : (isSmallScreen ? 15 : 16)
                    ),
                    decoration: InputDecoration(
                      hintText: 'あなたの考えを教えてください...',
                      hintStyle: TextStyle(
                        color: Colors.grey[400],
                        fontSize: isVerySmallScreen ? 14 : (isSmallScreen ? 15 : 16),
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: isVerySmallScreen ? 8 : 12,
                        vertical: isVerySmallScreen ? 8 : 12,
                      ),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                    maxLines: null,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (text) {
                      if (text.trim().isNotEmpty) {
                        onAnswerSubmitted(text.trim());
                        textController.clear();
                      }
                    },
                  ),
                ),
              ),
              SizedBox(width: isVerySmallScreen ? 6 : 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.purple,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: IconButton(
                  onPressed: () {
                    final text = textController.text.trim();
                    if (text.isNotEmpty) {
                      onAnswerSubmitted(text);
                      textController.clear();
                    }
                  },
                  icon: const Icon(Icons.send, color: Colors.white),
                  iconSize: isVerySmallScreen ? 16 : 18,
                ),
              ),
            ],
          ),
    );
  }
}
