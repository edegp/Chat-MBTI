import 'package:flutter/material.dart';

class NavigationButtons extends StatelessWidget {
  final bool isLoading;
  final bool canGoBack;
  final bool canGoForward;
  final VoidCallback? onGoBack;
  final VoidCallback? onGoForward;
  final String? currentQuestion;
  final int currentQuestionInPhase;

  const NavigationButtons({
    super.key,
    required this.isLoading,
    required this.canGoBack,
    required this.canGoForward,
    this.onGoBack,
    this.onGoForward,
    this.currentQuestion,
    required this.currentQuestionInPhase,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          // Back button
          IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: (!isLoading && canGoBack) ? onGoBack : null,
            tooltip: 'Go back',
          ),
          // Forward button
          IconButton(
            icon: const Icon(Icons.arrow_forward),
            onPressed: (!isLoading && canGoForward) ? onGoForward : null,
            tooltip: 'Go forward',
          ),
          const SizedBox(width: 8),
          // Question indicator
          Expanded(
            child: currentQuestion != null
              ? Text(
                  'Q$currentQuestionInPhase: $currentQuestion',
                  style: const TextStyle(fontSize: 14),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                )
              : const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}
