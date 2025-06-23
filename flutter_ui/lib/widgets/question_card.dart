import 'package:flutter/material.dart';

class QuestionCard extends StatelessWidget {
  final String question;
  final int currentQuestionInPhase;

  const QuestionCard({
    super.key,
    required this.question,
    required this.currentQuestionInPhase,
  });

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final screenHeight = MediaQuery.of(context).size.height;
    
    // More detailed screen size detection
    final isVerySmallScreen = screenWidth < 360; // Very small phones
    final isSmallScreen = screenWidth < 600;
    final isShortScreen = screenHeight < 700;
    
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(
        isVerySmallScreen ? 8 : (isSmallScreen ? 12 : 16)
      ),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: EdgeInsets.all(isVerySmallScreen ? 4 : 6),
                decoration: BoxDecoration(
                  color: Colors.purple,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Icon(
                  Icons.psychology,
                  size: isVerySmallScreen ? 12 : (isSmallScreen ? 14 : 16),
                  color: Colors.white,
                ),
              ),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  'Q$currentQuestionInPhase',
                  style: TextStyle(
                    fontSize: isVerySmallScreen ? 11 : (isSmallScreen ? 12 : 14),
                    fontWeight: FontWeight.bold,
                    color: Colors.purple,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: isVerySmallScreen ? 6 : (isSmallScreen ? 8 : 12)),
          Text(
            question,
            style: TextStyle(
              fontSize: isVerySmallScreen ? 14 : (isSmallScreen ? 16 : 18),
              height: isShortScreen ? 1.3 : 1.5,
              color: Colors.black87,
            ),
            textAlign: TextAlign.left,
            softWrap: true,
            overflow: TextOverflow.visible,
          ),
        ],
      ),
    );
  }
}
