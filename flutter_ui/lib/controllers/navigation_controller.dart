import '../models/navigation_state.dart';
import 'package:flutter/foundation.dart';


class NavigationController {
  List<NavigationState> _navigationHistory = [];
  int _currentNavigationIndex = -1;

  // Getters
  List<NavigationState> get navigationHistory => _navigationHistory;
  int get currentNavigationIndex => _currentNavigationIndex;

  // Save current state to navigation history
  void saveCurrentNavigationState({
    required int currentPhase,
    required int currentQuestionInPhase,
    required String currentQuestion,
    required List<String> currentOptions,
    required String? sessionId,
    required List<Map<String, dynamic>> currentSessionData,
    required List<String> questionHistory,
    required List<List<String>> optionsHistory,
  }) {
    final currentState = NavigationState(
      phase: currentPhase,
      questionInPhase: currentQuestionInPhase,
      question: currentQuestion,
      options: List<String>.from(currentOptions),
      sessionId: sessionId,
      sessionData: List<Map<String, dynamic>>.from(currentSessionData),
      questionHistory: List<String>.from(questionHistory),
      optionsHistory: List<List<String>>.from(optionsHistory),
    );

    // If we're not at the end of history, truncate future states
    if (_currentNavigationIndex < _navigationHistory.length - 1) {
      debugPrint('DEBUG: Truncating navigation history from index ${_currentNavigationIndex + 1}');
      _navigationHistory = _navigationHistory.sublist(0, _currentNavigationIndex + 1);
    }

    _navigationHistory.add(currentState);
    _currentNavigationIndex = _navigationHistory.length - 1;

    debugPrint('DEBUG: Saved navigation state - index: $_currentNavigationIndex, total: ${_navigationHistory.length}, question: $currentQuestion');
  }

  // Get state from navigation history
  NavigationState? getNavigationState(int index) {
    if (index >= 0 && index < _navigationHistory.length) {
      return _navigationHistory[index];
    }
    return null;
  }

  // Navigate back in history
  NavigationState? goBack() {
    debugPrint('DEBUG: goBack called - currentIndex: $_currentNavigationIndex, historyLength: ${_navigationHistory.length}');
    if (_currentNavigationIndex > 0) {
      _currentNavigationIndex--;
      debugPrint('DEBUG: Moving back to index $_currentNavigationIndex');
      return _navigationHistory[_currentNavigationIndex];
    }
    debugPrint('DEBUG: Cannot go back - at beginning of history');
    return null;
  }

  // Force navigation back by manually decrementing index
  void forceNavigateBack() {
    if (_currentNavigationIndex > 0) {
      _currentNavigationIndex--;
      debugPrint('DEBUG: Forced navigation back to index $_currentNavigationIndex');
    }
  }

  // Navigate forward in history
  NavigationState? goForward() {
    debugPrint('DEBUG: goForward called - currentIndex: $_currentNavigationIndex, historyLength: ${_navigationHistory.length}');
    if (_currentNavigationIndex < _navigationHistory.length - 1) {
      _currentNavigationIndex++;
      debugPrint('DEBUG: Moving forward to index $_currentNavigationIndex');
      return _navigationHistory[_currentNavigationIndex];
    }
    debugPrint('DEBUG: Cannot go forward - at end of history');
    return null;
  }

  // Check if we can go back
  bool canGoBack({
    required int currentQuestionInPhase,
    required int currentPhase,
  }) {
    return _currentNavigationIndex > 0 ||
           currentQuestionInPhase > 1 ||
           currentPhase > 1;
  }

  // Check if we can go forward
  bool canGoForward() {
    return _navigationHistory.isNotEmpty &&
           _currentNavigationIndex >= 0 &&
           _currentNavigationIndex < _navigationHistory.length - 1;
  }

  // Clear navigation history
  void clearNavigationHistory() {
    _navigationHistory.clear();
    _currentNavigationIndex = -1;
  }

  // Reset navigation for new phase
  void resetForNewPhase() {
    clearNavigationHistory();
  }
}
