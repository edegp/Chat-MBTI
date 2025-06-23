import 'package:flutter/material.dart';

class DataCollectionAppBar extends StatelessWidget {
  final bool isCollectionInProgress;
  final VoidCallback? onBack;
  final VoidCallback? onReset;
  final VoidCallback? onSignOut;

  const DataCollectionAppBar({
    super.key,
    required this.isCollectionInProgress,
    this.onBack,
    this.onReset,
    this.onSignOut,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          if (!isCollectionInProgress)
            IconButton(
              icon: const Icon(Icons.arrow_back, color: Colors.black54),
              onPressed: onBack,
            ),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.purple,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.analytics,
              color: Colors.white,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: GestureDetector(
              onTap: isCollectionInProgress ? onReset : null,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'データ収集',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Colors.black,
                    ),
                  ),
                  Text(
                    'MBTI質問応答データの収集',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.black54,
                    ),
                  ),
                ],
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.black54, size: 24),
            onPressed: onSignOut,
          ),
        ],
      ),
    );
  }
}
