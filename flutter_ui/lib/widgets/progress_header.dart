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
    return Container(
      padding: const EdgeInsets.all(20),
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
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    if (isCollectionInProgress) ...[
                      Text(
                        '${getCurrentElementType(currentPhase)} (${getCurrentCycle(currentPhase)}回目)',
                        style: const TextStyle(
                          fontSize: 16,
                          color: Colors.purple,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        '質問 $currentQuestionInPhase / ${DataCollectionConstants.questionsPerElement}',
                        style: const TextStyle(
                          fontSize: 16,
                          color: Colors.black54,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.purple,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '$collectedDataLength / ${DataCollectionConstants.totalPhases * DataCollectionConstants.questionsPerElement}',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
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
