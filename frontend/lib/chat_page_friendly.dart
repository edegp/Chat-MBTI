import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'result.dart';
import 'package:shared_preferences/shared_preferences.dart';

class FriendlyChatPage extends StatefulWidget {
  const FriendlyChatPage({super.key});

  @override
  State<FriendlyChatPage> createState() => _FriendlyChatPageState();
}

class _FriendlyChatPageState extends State<FriendlyChatPage> with TickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<JudgeAndReport> _reports = [];
  late Future<JudgeAndReport> _reportFuture;
  List<Future<JudgeAndReport>> _reportFutures = [];
  String? _currentQuestion;
  List<String> _currentOptions = [];
  List<Map<String, dynamic>> _chatHistory = [];
  double _progress = 0.0;
  int _questionNumber = 1;
  int _phase_per_question = 10; // 各フェーズの質問数（例: 8問）
  int _totalQuestions = 10 * 4;
  String? _sessionId;
  bool _isLoading = false;
  String? _error;
  bool _isCompleted = false;
  String? _completionMessage;
  bool _isRestoringHistory = false; // 履歴復元中フラグを追加

  // UI transition management - show only current phase conversations
  int _currentPhase = 1; // Phase 1: Q1-5, Phase 2: Q6-10, etc.

  late AnimationController _bubbleAnimController;
  late AnimationController _progressAnimController;

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    _bubbleAnimController.dispose();
    _progressAnimController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    // _startup();
    _isCompleted = false; // ← 追加: 初期化時に必ずリセット
    _bubbleAnimController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _progressAnimController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _checkExistingConversation();
  }

  Future<void> _startup() async {
    try {
      // await _apiService.startupSummaryApi(elementId: 3);
      if (!mounted) return;  // ← ここでガード
      // 必要ならここで setState(...)
    } catch (e, st) {
      if (!mounted) return;
      debugPrintStack(stackTrace: st, label: e.toString());
      // setState でエラー表示しても OK
    }
  }

  // 既存の会話をチェックして、続きから開始するか新しい会話を始める
  Future<void> _checkExistingConversation() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // 既存の進捗を確認
      final progressResponse = await _apiService.getProgress();
      final progressData = progressResponse['data'];
      if (progressData['progress'] > 0 && progressData['progress'] < 1.0) {
        // 途中の会話がある場合、状態を復元
        final questionNumber = progressData['question_number'] ?? 1;
        final currentPhase = ((questionNumber - 1) ~/ _phase_per_question) + 1;

        setState(() {
          _progress = (progressData['progress'] ?? 0.0).toDouble();
          _questionNumber = questionNumber;
          _totalQuestions = progressData['total_questions'] ?? _totalQuestions;
          _sessionId = progressData['session_id'];
          _currentPhase = currentPhase;
        });
        // デバッグ用ログ
        debugPrint('Restoring conversation: progress=$_progress, question=$_questionNumber/$_totalQuestions, phase=$_currentPhase, sessionId=$_sessionId');
        debugPrint('Browser Console: Restoring conversation: progress=$_progress, question=$_questionNumber/$_totalQuestions, phase=$_currentPhase');

        // プログレスバーアニメーションを復元された進捗値まで設定
        _progressAnimController.animateTo(_progress);

        // 会話履歴を復元
        await _restoreConversationHistory();

        // 復元後に現在の質問とオプションを取得
        _getCurrentQuestion();
        await _getOptions();

        // Stop loading after restoration
        setState(() {
          _isLoading = false;
        });

        // 復元メッセージを表示
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Phase $_currentPhase から続行 ($_questionNumber/$_totalQuestions)'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 3),
            ),
          );
        }
      } else if (progressData['progress'] >= 1.0) {
        // 完了した診断がある場合
        setState(() {
          _isCompleted = true;
          _completionMessage = '前回の診断が完了しています。新しい診断を開始できます。';
          _isLoading = false;
        });
      } else {
        // 新しい会話を開始
        await _startConversation();
      }
    } catch (e) {
      // エラーの場合は新しい会話を開始
      debugPrint('Progress check failed, starting new conversation: $e');
      await _startConversation();
    }
  }

  Future<void> _startConversation() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await _apiService.startConversation();
      final data = response['data'];

      setState(() {
        _currentQuestion = data['question'];
        _sessionId = data['session_id'];
        _isLoading = false;
        // Add question bubble if not duplicate
        final qText = data['question'];
        if (_chatHistory.isEmpty || _chatHistory.last['text'] != qText) {
          _chatHistory.add({
            'type': 'question',
            'text': qText,
            'timestamp': DateTime.now(),
          });
        }
      });

      _bubbleAnimController.forward();
      await _getOptions();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  // 新しい会話を強制的に開始（既存セッションを無視）
  Future<void> _startNewConversation() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _currentPhase = 1; // Reset to Phase 1 when starting new conversation
    });

    try {
      final response = await _apiService.startNewConversation();
      final data = response['data'];

      setState(() {
        _currentQuestion = data['question'];
        _sessionId = data['session_id'];
        _isLoading = false;
        final qText = data['question'];
        if (_chatHistory.isEmpty || _chatHistory.last['text'] != qText) {
          _chatHistory.add({
            'type': 'question',
            'text': qText,
            'timestamp': DateTime.now(),
          });
        }
      });

      _bubbleAnimController.forward();
      await _getOptions();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _getOptions() async {
    try {
      final response = await _apiService.getOptions();
      final data = response['data'];

      setState(() {
        _currentOptions = List<String>.from(data['options']);
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
      _error = null;
      _chatHistory.add({
        'type': 'answer',
        'text': answer,
        'timestamp': DateTime.now(),
      });
    });

    _textController.clear();

    try {
      // Resume conversation by submitting the answer
      final response = await _apiService.submitAnswer(answer);
      final data = response['data'];

      if (data['phase'] == 'question') {
        final newQuestionNumber = data['question_number'] ?? 1;
        final newPhase = ((newQuestionNumber - 1) ~/ _phase_per_question) + 1;

        // Check if we need to transition to a new phase (every _phase_per_question questions)
        if (newPhase > _currentPhase) {
          // Clear history when entering a new phase
          _reportFuture = _apiService.generateReport(_currentPhase);
          _reportFuture.then((report_json) {
            if (!mounted) return;
            setState(() {
              _reports.add(report_json);
            });
          });
          _reportFutures.add(_reportFuture);
          // if (_currentPhase == 1) {
          //   final future_startup = _apiService.startupSummaryApi(elementId: 4);
          // }

          setState(() {
            _chatHistory.clear();
            _currentPhase = newPhase;
          });

          // Show phase transition message
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Phase $_currentPhase開始 (質問 ${(newPhase-1)*_phase_per_question + 1}-${newPhase*_phase_per_question})'),
                backgroundColor: Colors.green,
                duration: const Duration(seconds: 2),
              ),
            );
          }
        }

        setState(() {
          _currentQuestion = data['question'];
          _progress = (data['progress'] ?? 0.0).toDouble();
          _questionNumber = newQuestionNumber;
          _totalQuestions = data['total_questions'] ?? _totalQuestions;
          _isLoading = false;
          final qText = data['question'];
          if (_chatHistory.isEmpty || _chatHistory.last['text'] != qText) {
            _chatHistory.add({
              'type': 'question',
              'text': qText,
              'timestamp': DateTime.now(),
            });
          }
        });

        // デバッグ用ログ
        debugPrint('Progress updated: $_progress, question: $_questionNumber/$_totalQuestions, Phase: $_currentPhase');
        debugPrint('Backend data: $data');
        debugPrint('Browser Console: Progress updated: $_progress, question: $_questionNumber/$_totalQuestions, Phase: $_currentPhase');
        debugPrint('Browser Console: Backend data: $data');

        // プログレスバーアニメーションを更新
        _progressAnimController.animateTo(_progress);

        // 明示的にプログレス情報を再取得して更新
        // Removed redundant explicit progress refresh to prevent off-by-one

        await _getOptions();
        _scrollToBottom();
      } else if (data['phase'] == 'diagnosis') {
          _reportFuture = _apiService.generateReport(_currentPhase);
          _reportFuture.then((report_json) {
            if (!mounted) return;
            setState(() {
              _reports.add(report_json);
            });
          });
          _reportFutures.add(_reportFuture);
          // show loading dot
          setState(() {
            _isLoading = false;
            _isCompleted = true;
            _completionMessage = data['message'];
            _isLoading = false;
          });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  // プログレス情報を明示的に更新する関数
  // ignore: unused_element
  Future<void> _updateProgress() async {
    try {
      final progressResponse = await _apiService.getProgress();
      final progressData = progressResponse['data'];

      setState(() {
        _progress = (progressData['progress'] ?? 0.0).toDouble();
        _questionNumber = progressData['question_number'] ?? 1;
        _totalQuestions = progressData['total_questions'] ?? _totalQuestions;
      });

      // デバッグ用ログ
      debugPrint('Progress refreshed: $_progress, question: $_questionNumber/$_totalQuestions');
      debugPrint('Browser Console: Progress refreshed: $_progress, question: $_questionNumber/$_totalQuestions');

      // プログレスバーアニメーションを最新の値で更新
      _progressAnimController.animateTo(_progress);
    } catch (e) {
      debugPrint('Failed to update progress: $e');
      debugPrint('Browser Console: Failed to update progress: $e');
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _signOut() async {
    await FirebaseAuth.instance.signOut();
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/');
    }
  }

  // 会話履歴を復元（elementごとに順次表示）
  Future<void> _restoreConversationHistory() async {
    try {
      final historyResponse = await _apiService.getConversationHistory();
      final historyData = historyResponse['data'];
      final history = historyData['history'] as List<dynamic>;

      // Determine phase boundaries for questions
      final phaseStartIndex = (_currentPhase - 1) * _phase_per_question;
      final phaseEndIndex = _currentPhase * _phase_per_question;
      final phaseStartQuestion = phaseStartIndex + 1;
      final phaseEndQuestion = phaseEndIndex;
      // Build filtered history based on phase boundaries
      final filteredHistory = <dynamic>[];
      int questionCount = 0;
      for (final msg in history) {
        if (msg['type'] == 'question') {
          questionCount++;
          if (questionCount >= phaseStartQuestion && questionCount <= phaseEndQuestion) {
            filteredHistory.add(msg);
          }
        } else if (msg['type'] == 'answer' &&
            filteredHistory.isNotEmpty &&
            filteredHistory.last['type'] == 'question') {
          filteredHistory.add(msg);
        }
      }

      // 履歴を順次復元（elementごとに表示）
      await _restoreHistoryStepByStep(filteredHistory);

    } catch (e) {
      debugPrint('Failed to restore conversation history: $e');
      // 履歴復元に失敗してもエラーにはせず、空の履歴で続行
      setState(() {
        _chatHistory = [];
      });
    }
  }

  // 履歴を段階的に復元する関数
  Future<void> _restoreHistoryStepByStep(List<dynamic> filteredHistory) async {
    // 復元開始
    setState(() {
      _chatHistory = [];
      _isRestoringHistory = true;
    });

    // 復元中であることをユーザーに示す
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: const [
              SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              ),
              SizedBox(width: 8),
              Text('会話を復元中...'),
            ],
          ),
          backgroundColor: Colors.blue,
          duration: Duration(milliseconds: filteredHistory.length * 600 + 1000),
        ),
      );
    }

    // 質問と回答をペアで順次追加
    for (int i = 0; i < filteredHistory.length; i++) {
      final msg = filteredHistory[i];

      // メッセージタイプに応じて表示タイミングを調整
      final isQuestion = msg['type'] == 'question';
      final delay = isQuestion ? 800 : 400; // 質問の方を少し長く表示

      // 新しいメッセージを追加
      setState(() {
        _chatHistory.add({
          'type': msg['type'],
          'text': msg['text'],
          'timestamp': DateTime.now(),
        });
      });

      // アニメーション効果のために待機
      await Future.delayed(Duration(milliseconds: delay));

      // バブルアニメーションを再生
      _bubbleAnimController.reset();
      _bubbleAnimController.forward();

      // スクロールを最下部に移動
      _scrollToBottom();

      // 次の要素がある場合は少し間隔を空ける
      if (i < filteredHistory.length - 1) {
        // 質問の後は回答を待つ感じで少し長めの間隔
        final nextMsg = filteredHistory[i + 1];
        final isNextAnswer = nextMsg['type'] == 'answer';
        final waitTime = (isQuestion && isNextAnswer) ? 300 : 200;
        await Future.delayed(Duration(milliseconds: waitTime));
      }
    }

    // 復元完了
    setState(() {
      _isRestoringHistory = false;
    });

    // 復元完了メッセージ
    if (mounted && filteredHistory.isNotEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('会話の復元が完了しました'),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  // 現在の質問のみを取得する関数（新しい会話を開始しない）
  void _getCurrentQuestion() {
    if (_chatHistory.isNotEmpty) {
      // Find last question bubble in history
      final lastQuestion = _chatHistory.lastWhere(
        (m) => m['type'] == 'question',
        orElse: () => {},
      );
      if (lastQuestion.isNotEmpty && lastQuestion.containsKey('text')) {
        setState(() {
          _currentQuestion = lastQuestion['text'] as String;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAF9F6), // ログイン画面と同じクリーム色
      body: SafeArea(
        child: Column(
          children: [
            _buildSimpleAppBar(),
            Expanded(
              child: !_isLoading ? _buildCompletionView() : _buildChatView(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSimpleAppBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: Colors.black,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(
              Icons.psychology,
              color: Colors.white,
              size: 20,
            ),
          ),
          const SizedBox(width: 8),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'MBTI診断AI',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Colors.black,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.black54, size: 24),
            onPressed: _showResetDialog,
            tooltip: 'リセット',
          ),
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.black54, size: 24),
            onPressed: _signOut,
            tooltip: 'サインアウト',
          ),
        ],
      ),
    );
  }

  // チャットリセット用のモーダルダイアログ
  void _showResetDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('診断をリセットしますか？'),
          content: const Text('現在の会話履歴と進捗がすべて消去され、最初から診断をやり直します。よろしいですか？'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: const Text('キャンセル'),
            ),
            TextButton(
              onPressed: () async {
                Navigator.of(context).pop();
                await _resetChat();
              },
              child: const Text('リセット', style: TextStyle(color: Colors.red)),
            ),
          ],
        );
      },
    );
  }

  // チャット状態をリセットして新しい会話を開始
  Future<void> _resetChat() async {
    // フィードバック送信済み状態もリセット
    if (_sessionId != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('feedback_sent_[200m${_sessionId!}[0m');
    }
    setState(() {
      _chatHistory = [];
      _progress = 0.0;
      _questionNumber = 1;
      _totalQuestions = 10 * 4;
      _sessionId = null;
      _isLoading = false;
      _error = null;
      _isCompleted = false;
      _completionMessage = null;
      _isRestoringHistory = false;
      _currentPhase = 1;
      _currentQuestion = null;
      _currentOptions = [];
    });
    await _startNewConversation();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('診断がリセットされました'),
          backgroundColor: Colors.red,
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  Widget _buildChatView() {
    return Column(
      children: [
        // 進捗バー（復元中は復元状態を表示）
        _isRestoringHistory ? _buildRestoringProgressBar() : _buildCompactProgressBar(),

        // チャット履歴エリア（より広く）
        Expanded(
          child: Container(
            margin: const EdgeInsets.fromLTRB(8, 4, 8, 0),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Column(
              children: [
                // チャット履歴
                Expanded(
                  child: ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: _chatHistory.length,
                    itemBuilder: (context, index) {
                      final message = _chatHistory[index];
                      return _buildChatBubble(message, index);
                    },
                  ),
                ),

                // エラー表示
                if (_error != null) _buildErrorView(),

                // 回答オプション（復元中は非表示）
                if (_currentQuestion != null && _currentOptions.isNotEmpty && !_isLoading && !_isRestoringHistory)
                  _buildOptions(),

                // 入力エリア（復元中は非表示）
                if (_currentQuestion != null && !_isLoading && !_isRestoringHistory)
                  _buildInputArea(),

                // ローディング
                if (_isLoading && !_isCompleted) _buildLoading(),

                // 性格診断ローディング
                if (_isCompleted && _completionMessage == null) _buildDiagnosisLoading(),

                // 履歴復元中インジケーター
                if (_isRestoringHistory) _buildRestoringIndicator(),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDiagnosisLoading() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              '性格診断を生成中...',
              style: TextStyle(fontSize: 16, color: Colors.black54),
            ),
            const SizedBox(height: 8),
            CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.black),
              strokeWidth: 2,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCompactProgressBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Phase $_currentPhase',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: Colors.black,
                    ),
                  ),
                  Text(
                    '質問 $_questionNumber / $_totalQuestions',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.black87,
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${(_progress * 100).toInt()}%',
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
          Container(
            height: 6,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(3),
              color: Colors.grey[200],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: LinearProgressIndicator(
                value: _progress,
                backgroundColor: Colors.transparent,
                valueColor: const AlwaysStoppedAnimation<Color>(
                  Colors.black,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRestoringProgressBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.blue[200]!),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Phase $_currentPhase - 復元中',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: Colors.blue[700],
                    ),
                  ),
                  Text(
                    '会話履歴を復元しています...',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.blue[800],
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.blue[600],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      width: 12,
                      height: 12,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    ),
                    const SizedBox(width: 6),
                    const Text(
                      '復元中',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            height: 6,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(3),
              color: Colors.blue[100],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: LinearProgressIndicator(
                backgroundColor: Colors.transparent,
                valueColor: AlwaysStoppedAnimation<Color>(
                  Colors.blue[600]!,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChatBubble(Map<String, dynamic> message, int index) {
    final isQuestion = message['type'] == 'question';
    final text = message['text'] as String;

    return AnimatedContainer(
      duration: Duration(milliseconds: 300 + (index * 50)),
      curve: Curves.easeOut,
      margin: const EdgeInsets.only(bottom: 16),
      child: AnimatedOpacity(
        duration: Duration(milliseconds: 400 + (index * 50)),
        opacity: 1.0,
        child: Transform.translate(
          offset: Offset(0, 0),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
          if (isQuestion) ...[
            // AI診断アバター
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(
                Icons.psychology,
                size: 18,
                color: Colors.white,
              ),
            ),
            const SizedBox(width: 8),
            // 質問メッセージ（LINEスタイル）
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(4),
                    topRight: Radius.circular(16),
                    bottomLeft: Radius.circular(16),
                    bottomRight: Radius.circular(16),
                  ),
                ),
                child: Text(
                  text,
                  style: const TextStyle(
                    fontSize: 15,
                    height: 1.35,
                    color: Colors.black87,
                  ),
                ),
              ),
            ),
          ] else ...[
            // ユーザーメッセージを右寄せ（インスタ風）
            const Expanded(child: SizedBox()),
            Container(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(16),
                  topRight: Radius.circular(4),
                  bottomLeft: Radius.circular(16),
                  bottomRight: Radius.circular(16),
                ),
              ),
              child: Text(
                text,
                style: const TextStyle(
                  fontSize: 15,
                  height: 1.35,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(width: 8),
            // ユーザーアバター
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: Colors.grey[400],
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                Icons.person,
                size: 18,
                color: Colors.grey[600],
              ),
            ),
          ],
        ],
      ),
        ),
      ),
    );
  }

  Widget _buildOptions() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '選択肢から選ぶ',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 6),
          ..._currentOptions.asMap().entries.map((entry) {
            final index = entry.key;
            final option = entry.value;
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              child: InkWell(
                onTap: () => _submitAnswer(option),
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: Colors.grey[300]!,
                      width: 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 24,
                        height: 24,
                        decoration: BoxDecoration(
                          color: Colors.black,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Center(
                          child: Text(
                            String.fromCharCode(65 + (index as int)), // A, B, C...
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          option,
                          style: const TextStyle(
                            fontSize: 14,
                            height: 1.35,
                            color: Colors.black87,
                          ),
                        ),
                      )
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

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        border: Border(
          top: BorderSide(color: Colors.grey[200]!),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '自由に回答する',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  child: TextField(
                    controller: _textController,
                    style: const TextStyle(fontSize: 16),
                    decoration: InputDecoration(
                      hintText: 'あなたの考えを教えてください...',
                      hintStyle: TextStyle(
                        color: Colors.grey[400],
                        fontSize: 16,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 12,
                      ),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                    maxLines: null,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (text) {
                      if (text.trim().isNotEmpty) {
                        _submitAnswer(text.trim());
                      }
                    },
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: IconButton(
                  onPressed: () {
                    final text = _textController.text.trim();
                    if (text.isNotEmpty) {
                      _submitAnswer(text);
                    }
                  },
                  icon: const Icon(Icons.send, color: Colors.white),
                  iconSize: 18,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLoading() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(Colors.black),
            ),
          ),
          const SizedBox(width: 8),
          const Text(
            'AIが分析中です...',
            style: TextStyle(
              color: Colors.black87,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorView() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.red[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.red[200]!),
      ),
      child: Row(
        children: [
          Icon(Icons.error, color: Colors.red[600]),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'エラー: $_error',
              style: TextStyle(
                color: Colors.red[800],
                fontSize: 16,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCompletionView() {
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final result = await Navigator.of(context).pushNamed("/result", arguments: {
        'reports': _reports,
        'reportFutures': _reportFutures,
      });
      if (result == true) {
        _resetChat();
      }
    });
    return const Center(
      child: CircularProgressIndicator(),
    );
  }

  Widget _buildRestoringIndicator() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
            ),
          ),
          const SizedBox(width: 8),
          const Text(
            '会話を復元中です...',
            style: TextStyle(
              color: Colors.black87,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }
}
