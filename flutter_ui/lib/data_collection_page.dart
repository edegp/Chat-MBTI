// ignore_for_file: constant_identifier_names, prefer_final_fields, avoid_print, use_build_context_synchronously, non_constant_identifier_names, unused_local_variable

import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';

// Import new components
import 'models/navigation_state.dart';
import 'constants/data_collection_constants.dart';
import 'controllers/navigation_controller.dart';
import 'controllers/data_collection_controller.dart';
import 'widgets/data_collection_app_bar.dart';
import 'widgets/progress_header.dart';
import 'widgets/navigation_buttons.dart';
import 'widgets/question_card.dart';
import 'widgets/answer_options.dart';
import 'widgets/custom_answer_input.dart';
import 'widgets/start_view.dart';

class DataCollectionPage extends StatefulWidget {
  const DataCollectionPage({super.key});

  @override
  State<DataCollectionPage> createState() => _DataCollectionPageState();
}

class _DataCollectionPageState extends State<DataCollectionPage> {
  // Controllers
  final NavigationController _navigationController = NavigationController();
  final DataCollectionController _dataController = DataCollectionController();
  final TextEditingController _textController = TextEditingController();
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _personalityController = TextEditingController();

  String? _personalityCode;

  // Current state
  int _currentPhase = 1;
  int _currentQuestionInPhase = 1;
  String? _currentQuestion;
  List<String> _currentOptions = [];
  String? _sessionId;
  bool _isLoading = false;
  String _loadingMessage = '読み込み中...';
  bool _isCollectionInProgress = false;
  String? _error;
  String? _participantName;

  // Data storage
  List<Map<String, dynamic>> _collectedData = [];
  List<Map<String, dynamic>> _currentSessionData = [];
  List<List<String>> _optionsHistory = [];
  List<String> _questionHistory = [];

  // History per phase for session data and options, to support back navigation across phase boundaries
  List<List<Map<String, dynamic>>> _phaseSessionHistory = [];
  List<List<List<String>>> _phaseOptionsHistory = [];
  List<List<String>> _phaseQuestionHistory = [];

  // Lazy sync state management
  bool _hasServerDesync = false;
  String? _lastAnswerBeforeBack;

  @override
  void initState() {
    super.initState();
    _restoreProgressFromPrefs();
  }

  @override
  void dispose() {
    _textController.dispose();
    _nameController.dispose();
    _personalityController.dispose();
    super.dispose();
  }

  Future<void> _restoreProgressFromPrefs() async {
    final savedData = await _dataController.restoreProgressFromPrefs();
    if (savedData != null) {
      setState(() {
        _participantName = savedData['participantName'];
        _personalityCode = savedData['personalityCode'];
        if (_personalityCode != null) {
          _personalityController.text = _personalityCode!;
        }
        _currentPhase = savedData['currentPhase'] ?? 1;
        _collectedData = List<Map<String, dynamic>>.from(savedData['collectedData'] ?? []);
        _isCollectionInProgress = true;
      });
      // Resume from where we left off
      await _startNewPhase();
    }
  }

  Future<void> _startDataCollection() async {
    // Validate participant name
    if (_nameController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('データ利用に同意の上、参加者名を入力してください'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    // Validate personality code
    if (_personalityController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('16性格コードを入力してください'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() {
      _participantName = _nameController.text.trim();
      _personalityCode = _personalityController.text.trim().toUpperCase();
      _isCollectionInProgress = true;
      _currentPhase = 1;
      _currentQuestionInPhase = 1;
      _collectedData.clear();
      _error = null;
      _hasServerDesync = false;
      _lastAnswerBeforeBack = null;
    });

    await _startNewPhase();
  }

  Future<void> _startNewPhase() async {
    setState(() {
      _isLoading = true;
      _loadingMessage = 'フェーズ $_currentPhase を開始中...';
      _currentQuestionInPhase = 1;
      _currentSessionData.clear();
      _optionsHistory.clear();
      _questionHistory.clear();
      _hasServerDesync = false;
      _lastAnswerBeforeBack = null;
    });

    _navigationController.resetForNewPhase();

    try {
      final elementId = _dataController.getCurrentElementId(_currentPhase);
      final response = await _dataController.startNewConversation(elementId: elementId);

      setState(() {
        _currentQuestion = response['data']['question'];
        _sessionId = response['data']['session_id'];
        _loadingMessage = '選択肢を生成中...';
      });

      if (_currentQuestion != null) _questionHistory.add(_currentQuestion!);
      await _getOptions();
      setState(() {
        _optionsHistory.add(_currentOptions);
        _isLoading = false;
      });

      _saveCurrentNavigationState();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _getOptions() async {
    try {
      final response = await _dataController.getOptions();
      final options = List<String>.from(response['data']['options'] ?? []);
      setState(() {
        _currentOptions = options;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    }
  }

  Future<void> _submitAnswer(String answer) async {
    setState(() {
      _isLoading = true;
      _loadingMessage = '回答を送信中...';
      _error = null;
    });

    try {
      // Debug current state
      print('DEBUG: submitAnswer called');
      print('DEBUG: _hasServerDesync = $_hasServerDesync');
      print('DEBUG: _lastAnswerBeforeBack = $_lastAnswerBeforeBack');
      print('DEBUG: answer = $answer');
      print('DEBUG: navigationIndex = ${_navigationController.currentNavigationIndex}');
      print('DEBUG: navigationHistoryLength = ${_navigationController.navigationHistory.length}');

      // Check if we need to sync server state after going back
      // We need to sync if we're in a desync state, regardless of the answer choice
      bool needsServerSync = _hasServerDesync &&
                           _navigationController.currentNavigationIndex >= 0 &&
                           _navigationController.currentNavigationIndex < _navigationController.navigationHistory.length - 1;

      print('DEBUG: needsServerSync = $needsServerSync');

      // Calculate the number of steps to undo based on navigation position
      int stepsToUndo = 0;
      if (needsServerSync) {
        stepsToUndo = _navigationController.navigationHistory.length - 1 - _navigationController.currentNavigationIndex;
      }
      print('DEBUG: stepsToUndo = $stepsToUndo');

      if (needsServerSync && stepsToUndo > 0) {
        // Undo multiple steps on server before proceeding with new answer
        try {
          print('DEBUG: Calling undoLastAnswer API with $stepsToUndo steps...');
          await _dataController.undoLastAnswer(steps: stepsToUndo);
          print('DEBUG: undoLastAnswer API call successful for $stepsToUndo steps');
          // Reset sync flags
          _hasServerDesync = false;
          _lastAnswerBeforeBack = null;
        } catch (e) {
          // If undo fails, log but continue - might be recoverable
          print('Warning: Failed to undo last $stepsToUndo step(s) on server: $e');
        }
      } else {
        print('DEBUG: Skipping server sync - needsServerSync = $needsServerSync, stepsToUndo = $stepsToUndo');
      }

      print(_currentQuestion);
      final newEntry = {
        'participant_name': _participantName,
        'phase': _currentPhase,
        'element_type': _dataController.getCurrentElementType(_currentPhase),
        'cycle_number': _dataController.getCurrentCycle(_currentPhase),
        'question_number_in_phase': _currentQuestionInPhase,
        'question': _currentQuestion,
        'answer': answer,
        'timestamp': DateTime.now().toIso8601String(),
        'session_id': _sessionId,
      };
      _currentSessionData.add(newEntry);
      _optionsHistory.add(_currentOptions); // push options history

      // If we're in a desync state and submitting a different answer, clear future navigation history
      if (_hasServerDesync && _lastAnswerBeforeBack != null && _lastAnswerBeforeBack != answer) {
        print('DEBUG: Clearing future navigation history due to answer change');
        // This will be handled by the navigation controller when saving the new state
      }

      // Reset sync state since we're now in sync with a new answer
      if (needsServerSync || (_hasServerDesync && _lastAnswerBeforeBack != answer)) {
        _hasServerDesync = false;
        _lastAnswerBeforeBack = null;
      }

      // Save current navigation state before proceeding
      _saveCurrentNavigationState();

      if (_currentQuestionInPhase < DataCollectionConstants.questionsPerElement) {
        setState(() {
          _loadingMessage = '次の質問を生成中...';
        });
        final response = await _dataController.submitAnswer(answer);

        setState(() {
          _currentQuestion = response['data']['question'];
          _currentQuestionInPhase++;
          _loadingMessage = '選択肢を生成中...';
        });
        // 新しい質問を履歴に追加
        if (_currentQuestion != null) _questionHistory.add(_currentQuestion!);
        await _getOptions();

        setState(() {
          _isLoading = false;
        });

        // Save navigation state after getting new question
        _saveCurrentNavigationState();
      } else {
        setState(() {
          _loadingMessage = 'フェーズ $_currentPhase を完了中...';
        });
        await _completePhase();
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _completePhase() async {
    await _dataController.uploadPhaseCsvToGcs(
      phaseNumber: _currentPhase,
      currentSessionData: _currentSessionData,
      participantName: _participantName,
      personalityCode: _personalityCode,
    );

    _collectedData.addAll(_currentSessionData);

    // Save completed phase session data and options history for back navigation
    _phaseSessionHistory.add(List<Map<String, dynamic>>.from(_currentSessionData));
    _phaseOptionsHistory.add(List<List<String>>.from(_optionsHistory));
    _phaseQuestionHistory.add(List<String>.from(_questionHistory));

    if (_currentPhase < DataCollectionConstants.totalPhases) {
      // Move to next phase
      setState(() {
        _currentPhase++;
      });

      // Show phase completion message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('フェーズ ${_currentPhase - 1} 完了！フェーズ $_currentPhase を開始します...'),
          backgroundColor: Colors.green,
          duration: const Duration(seconds: 3),
        ),
      );

      await Future.delayed(const Duration(seconds: 1));
      await _startNewPhase();
    } else {
      // All phases completed
      await _completeDataCollection();
    }
    await _saveProgressToPrefs();
  }

  Future<void> _completeDataCollection() async {
    setState(() {
      _isCollectionInProgress = false;
      _isLoading = false;
    });

    // Upload all data to GCS
    await _dataController.uploadCsvToGcs(
      collectedData: _collectedData,
      participantName: _participantName,
      personalityCode: _personalityCode,
    );

    // Show completion message
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('データ収集完了！ありがとうございました'),
        backgroundColor: Colors.green,
        duration: Duration(seconds: 4),
      ),
    );

    // Clear the session data and prefs
    await _dataController.clearPrefs();
    await _goToStart();
  }

  void _downloadCSV() {
    _dataController.downloadCSV(
      collectedData: _collectedData,
      participantName: _participantName,
      personalityCode: _personalityCode,
    );
  }

  void _signOut() async {
    await _dataController.signOut();
    if (kIsWeb) {
      // For web, just go to home
      Navigator.of(context).pushReplacementNamed('/');
    } else {
      // For other platforms, exit app
      Navigator.of(context).pushReplacementNamed('/');
    }
  }

  Future<void> _saveProgressToPrefs() async {
    await _dataController.saveProgressToPrefs(
      participantName: _participantName,
      personalityCode: _personalityCode,
      currentPhase: _currentPhase,
      collectedData: _collectedData,
    );
  }

  Future<void> _confirmReset() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('データをリセットしますか？'),
        content: const Text('これまでのデータがすべて削除されます。この操作は取り消せません。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('キャンセル'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('リセット'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _goToStart();
    }
  }

  Future<void> _goToStart() async {
    await _dataController.clearPrefs();
    setState(() {
      _isCollectionInProgress = false;
      _currentPhase = 1;
      _currentQuestionInPhase = 1;
      _currentQuestion = null;
      _currentOptions.clear();
      _sessionId = null;
      _isLoading = false;
      _error = null;
      _participantName = null;
      _personalityCode = null;
      _collectedData.clear();
      _currentSessionData.clear();
      _optionsHistory.clear();
      _questionHistory.clear();
      _phaseSessionHistory.clear();
      _phaseOptionsHistory.clear();
      _phaseQuestionHistory.clear();
      _hasServerDesync = false;
      _lastAnswerBeforeBack = null;
    });
    _nameController.clear();
    _personalityController.clear();
  }

  void _saveCurrentNavigationState() {
    if (_currentQuestion != null) {
      _navigationController.saveCurrentNavigationState(
        currentPhase: _currentPhase,
        currentQuestionInPhase: _currentQuestionInPhase,
        currentQuestion: _currentQuestion!,
        currentOptions: _currentOptions,
        sessionId: _sessionId,
        currentSessionData: _currentSessionData,
        questionHistory: _questionHistory,
        optionsHistory: _optionsHistory,
      );
    }
  }

  void _restoreNavigationState(NavigationState state) {
    setState(() {
      _currentPhase = state.phase;
      _currentQuestionInPhase = state.questionInPhase;
      _currentQuestion = state.question;
      _currentOptions = state.options;
      _sessionId = state.sessionId;
      _currentSessionData = state.sessionData;
      _questionHistory = state.questionHistory;
      _optionsHistory = state.optionsHistory;
    });
  }

  Future<void> _goBack() async {
    setState(() {
      _isLoading = true;
      _loadingMessage = '前の質問に戻っています...';
    });

    try {
      final canGoBack = _navigationController.canGoBack(
        currentQuestionInPhase: _currentQuestionInPhase,
        currentPhase: _currentPhase,
      );

      if (!canGoBack) {
        setState(() {
          _isLoading = false;
        });
        return;
      }

      // Set the last answer for potential server sync before going back
      if (_currentSessionData.isNotEmpty && !_hasServerDesync) {
        final lastEntry = _currentSessionData.last;
        _lastAnswerBeforeBack = lastEntry['answer'] as String?;
        print('DEBUG: Set _lastAnswerBeforeBack = $_lastAnswerBeforeBack');
      }

      // Try to use navigation controller first
      final previousState = _navigationController.goBack();
      if (previousState != null) {
        // Use navigation controller state
        print('DEBUG: Going back using navigation controller to question ${previousState.questionInPhase} in phase ${previousState.phase}');
        _restoreNavigationState(previousState);
        setState(() {
          _hasServerDesync = true;
          _isLoading = false;
        });
        return;
      } else {
        print('DEBUG: Navigation controller goBack returned null, using fallback logic');
      }

      // Fallback to manual navigation logic for phase boundaries
      // Check if going back across phases
      bool crossingPhases = _currentQuestionInPhase == 1 && _currentPhase > 1;

      if (crossingPhases) {
        // Going back to previous phase
        int previousPhase = _currentPhase - 1;
        if (_phaseSessionHistory.length >= previousPhase) {
          // Restore from phase history
          setState(() {
            _currentPhase = previousPhase;
            _currentQuestionInPhase = DataCollectionConstants.questionsPerElement;
            _currentSessionData = List<Map<String, dynamic>>.from(_phaseSessionHistory[previousPhase - 1]);
            _optionsHistory = List<List<String>>.from(_phaseOptionsHistory[previousPhase - 1]);
            _questionHistory = List<String>.from(_phaseQuestionHistory[previousPhase - 1]);
            _currentQuestion = _questionHistory.isNotEmpty ? _questionHistory.last : null;
            _currentOptions = _optionsHistory.isNotEmpty ? _optionsHistory.last : [];
            _hasServerDesync = true;
          });
          // Force navigation controller to update its index
          _navigationController.forceNavigateBack();
        }
      } else {
        // Going back within the same phase
        if (_currentQuestionInPhase > 1) {
          setState(() {
            _currentQuestionInPhase--;
            _currentQuestion = _questionHistory.isNotEmpty ? _questionHistory[_currentQuestionInPhase - 1] : null;
            _currentOptions = _optionsHistory.isNotEmpty ? _optionsHistory[_currentQuestionInPhase - 1] : [];
            _hasServerDesync = true;
          });
          // Force navigation controller to update its index
          _navigationController.forceNavigateBack();
        }
      }

      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _goForward() {
    print('DEBUG: Attempting to go forward - canGoForward: ${_canGoForward()}');
    final state = _navigationController.goForward();
    if (state != null) {
      print('DEBUG: Going forward to question ${state.questionInPhase} in phase ${state.phase}');
      _restoreNavigationState(state);
      setState(() {
        _hasServerDesync = true; // Mark as desync since we're going to a previous state
      });
    } else {
      print('DEBUG: No forward state available');
    }
  }

  bool _canGoBack() {
    return _navigationController.canGoBack(
      currentQuestionInPhase: _currentQuestionInPhase,
      currentPhase: _currentPhase,
    );
  }

  bool _canGoForward() {
    final canForward = _navigationController.canGoForward();
    print('DEBUG: canGoForward = $canForward, navigationIndex = ${_navigationController.currentNavigationIndex}, historyLength = ${_navigationController.navigationHistory.length}');
    return canForward;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAF9F6),
      body: SafeArea(
        child: Column(
          children: [
            DataCollectionAppBar(
              isCollectionInProgress: _isCollectionInProgress,
              onReset: _confirmReset,
              onSignOut: _signOut,
            ),
            Expanded(        child: Container(
          margin: EdgeInsets.all(
            MediaQuery.of(context).size.width < 360 ? 8 : 
            MediaQuery.of(context).size.width < 600 ? 12 : 16
          ),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 10,
                offset: const Offset(0, 2),
              ),
            ],
          ),
                child: Column(
                  children: [
                    ProgressHeader(
                      currentPhase: _currentPhase,
                      currentQuestionInPhase: _currentQuestionInPhase,
                      isCollectionInProgress: _isCollectionInProgress,
                      collectedDataLength: _collectedData.length,
                      getCurrentElementType: (phase) => _dataController.getCurrentElementType(phase),
                      getCurrentCycle: (phase) => _dataController.getCurrentCycle(phase),
                    ),
                    Expanded(
                      child: _isCollectionInProgress
                          ? _buildCollectionView()
                          : StartView(
                              nameController: _nameController,
                              personalityController: _personalityController,
                              personalityCode: _personalityCode,
                              hasCollectedData: _collectedData.isNotEmpty,
                              isLoading: _isLoading,
                              onPersonalityCodeChanged: (value) {
                                setState(() {
                                  _personalityCode = value;
                                  _personalityController.text = value ?? '';
                                });
                              },
                              onStartDataCollection: _startDataCollection,
                              onDownloadCSV: _downloadCSV,
                            ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCollectionView() {
    return Column(
      children: [
        NavigationButtons(
          canGoBack: _canGoBack(),
          canGoForward: _canGoForward(),
          isLoading: _isLoading,
          currentQuestion: _currentQuestion,
          currentQuestionInPhase: _currentQuestionInPhase,
          onGoBack: _goBack,
          onGoForward: _goForward,
        ),
        Expanded(
          child: _isLoading 
            ? Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.purple),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      _loadingMessage,
                      style: const TextStyle(
                        fontSize: 16,
                        color: Colors.purple,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              )
            : SingleChildScrollView(
                padding: EdgeInsets.all(
                  MediaQuery.of(context).size.width < 360 ? 12 : 
                  MediaQuery.of(context).size.width < 600 ? 16 : 20
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (_currentQuestion != null)
                      QuestionCard(
                        question: _currentQuestion!,
                        currentQuestionInPhase: _currentQuestionInPhase,
                      ),
                    if (_error != null) ...[
                      const SizedBox(height: 20),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.red[50],
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.red[200]!),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.error_outline,
                              color: Colors.red[700],
                              size: 20,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _error!,
                                style: TextStyle(
                                  color: Colors.red[700],
                                  fontSize: 14,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
        ),
        if (_currentOptions.isNotEmpty && !_isLoading)
          AnswerOptions(
            options: _currentOptions,
            onAnswerSelected: _submitAnswer,
          ),
        if (_currentQuestion != null && !_isLoading)
          CustomAnswerInput(
            textController: _textController,
            onAnswerSubmitted: _submitAnswer,
          ),
      ],
    );
  }
}
