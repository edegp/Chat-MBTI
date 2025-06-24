import 'package:flutter/material.dart';

class AnswerOptions extends StatelessWidget {
  final List<String> options;
  final Function(String) onAnswerSelected;

  const AnswerOptions({
    super.key,
    required this.options,
    required this.onAnswerSelected,
  });

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final screenHeight = MediaQuery.of(context).size.height;
    
    // More detailed screen size detection
    final isVerySmallScreen = screenWidth < 360;
    final isSmallScreen = screenWidth < 600;
    final isShortScreen = screenHeight < 700;
    
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isVerySmallScreen ? 8 : (isSmallScreen ? 12 : 16),
        vertical: isVerySmallScreen ? 8 : (isSmallScreen ? 12 : 16),
      ),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        border: Border(
          top: BorderSide(color: Colors.grey[200]!),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '選択肢から選ぶ',
            style: TextStyle(
              fontSize: isVerySmallScreen ? 12 : (isSmallScreen ? 14 : 16),
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: isVerySmallScreen ? 6 : (isSmallScreen ? 8 : 12)),
          ...options.asMap().entries.map((entry) {
            final index = entry.key;
            final option = entry.value;

            return Container(
              margin: EdgeInsets.only(
                bottom: isVerySmallScreen ? 4 : (isSmallScreen ? 6 : 8)
              ),
              child: InkWell(
                onTap: () => onAnswerSelected(option),
                borderRadius: BorderRadius.circular(8),
                child: Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(
                    isVerySmallScreen ? 8 : (isSmallScreen ? 10 : 12)
                  ),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: Colors.grey[300]!,
                      width: 1,
                    ),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: isVerySmallScreen ? 18 : (isSmallScreen ? 20 : 24),
                        height: isVerySmallScreen ? 18 : (isSmallScreen ? 20 : 24),
                        decoration: BoxDecoration(
                          color: Colors.purple,
                          borderRadius: BorderRadius.circular(
                            isVerySmallScreen ? 9 : (isSmallScreen ? 10 : 12)
                          ),
                        ),
                        child: Center(
                          child: Text(
                            String.fromCharCode(65 + index), // A, B, C...
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: isVerySmallScreen ? 10 : (isSmallScreen ? 12 : 14),
                            ),
                          ),
                        ),
                      ),
                      SizedBox(width: isVerySmallScreen ? 6 : (isSmallScreen ? 8 : 12)),
                      Expanded(
                        child: Text(
                          option,
                          style: TextStyle(
                            fontSize: isVerySmallScreen ? 12 : (isSmallScreen ? 14 : 16),
                            height: isShortScreen ? 1.3 : 1.5,
                            color: Colors.black87,
                          ),
                          textAlign: TextAlign.left,
                          softWrap: true,
                          overflow: TextOverflow.visible,
                        ),
                      ),
                      Icon(
                        Icons.arrow_forward_ios,
                        size: isVerySmallScreen ? 10 : (isSmallScreen ? 12 : 14),
                        color: Colors.grey,
                      ),
                    ],
                  ),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}
