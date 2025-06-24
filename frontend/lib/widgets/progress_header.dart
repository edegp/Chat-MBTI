import 'package:flutter/material.dart';
import '../constants/data_collection_constants.dart';

class ProgressHeader extends StatelessWidget {
  final int currentPhase;
  final int currentQuestionInPhase;
  final int collectedDataLength;
  final bool isCollectionInProgress;
  final String Function(int) getCurrentElementType;
  final int Function(int) getCurrentCycle;

  const ProgressHeader({
    super.key,
    required this.currentPhase,
    required this.currentQuestionInPhase,
    required this.collectedDataLength,
    required this.isCollectionInProgress,
    required this.getCurrentElementType,
    required this.getCurrentCycle,
  });

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final isVerySmallScreen = screenWidth < 360;
    final isSmallScreen = screenWidth < 600;
    
    return Container(
      padding: EdgeInsets.all(
        isVerySmallScreen ? 12 : (isSmallScreen ? 16 : 18)
      ),
      decoration: BoxDecoration(
        color: Colors.purple[50],
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(20),
          topRight: Radius.circular(20),
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'フェーズ $currentPhase / ${DataCollectionConstants.totalPhases}',
                      style: TextStyle(
                        fontSize: isVerySmallScreen ? 16 : (isSmallScreen ? 17 : 18),
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    if (isCollectionInProgress) ...[
                      SizedBox(height: isVerySmallScreen ? 2 : 4),
                      Text(
                        '${getCurrentElementType(currentPhase)} (${getCurrentCycle(currentPhase)}回目)',
                        style: TextStyle(
                          fontSize: isVerySmallScreen ? 14 : (isSmallScreen ? 15 : 16),
                          color: Colors.purple,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      SizedBox(height: isVerySmallScreen ? 1 : 2),
                      Text(
                        '質問 $currentQuestionInPhase / ${DataCollectionConstants.questionsPerElement}',
                        style: TextStyle(
                          fontSize: isVerySmallScreen ? 14 : (isSmallScreen ? 15 : 16),
                          color: Colors.black54,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(
                  horizontal: isVerySmallScreen ? 8 : 12,
                  vertical: isVerySmallScreen ? 4 : 6,
                ),
                decoration: BoxDecoration(
                  color: Colors.purple,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '$collectedDataLength / ${DataCollectionConstants.totalPhases * DataCollectionConstants.questionsPerElement}',
                  style: TextStyle(
                    fontSize: isVerySmallScreen ? 12 : 14,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: isVerySmallScreen ? 8 : 10),
          LinearProgressIndicator(
            value: collectedDataLength / (DataCollectionConstants.totalPhases * DataCollectionConstants.questionsPerElement),
            backgroundColor: Colors.purple[100],
            valueColor: const AlwaysStoppedAnimation<Color>(Colors.purple),
          ),
        ],
      ),
    );
  }
}
