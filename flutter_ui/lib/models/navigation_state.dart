// Navigation state for tracking forward/backward movement
class NavigationState {
  final int phase;
  final int questionInPhase;
  final String question;
  final List<String> options;
  final String? sessionId;
  final List<Map<String, dynamic>> sessionData;
  final List<String> questionHistory;
  final List<List<String>> optionsHistory;

  NavigationState({
    required this.phase,
    required this.questionInPhase,
    required this.question,
    required this.options,
    this.sessionId,
    required this.sessionData,
    required this.questionHistory,
    required this.optionsHistory,
  });

  NavigationState copyWith({
    int? phase,
    int? questionInPhase,
    String? question,
    List<String>? options,
    String? sessionId,
    List<Map<String, dynamic>>? sessionData,
    List<String>? questionHistory,
    List<List<String>>? optionsHistory,
  }) {
    return NavigationState(
      phase: phase ?? this.phase,
      questionInPhase: questionInPhase ?? this.questionInPhase,
      question: question ?? this.question,
      options: options ?? this.options,
      sessionId: sessionId ?? this.sessionId,
      sessionData: sessionData ?? this.sessionData,
      questionHistory: questionHistory ?? this.questionHistory,
      optionsHistory: optionsHistory ?? this.optionsHistory,
    );
  }
}
