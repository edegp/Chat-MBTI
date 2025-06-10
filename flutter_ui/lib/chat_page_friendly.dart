import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'package:firebase_auth/firebase_auth.dart';

class FriendlyChatPage extends StatefulWidget {
  const FriendlyChatPage({super.key});

  @override
  State<FriendlyChatPage> createState() => _FriendlyChatPageState();
}

class _FriendlyChatPageState extends State<FriendlyChatPage> with TickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  String? _currentQuestion;
  List<String> _currentOptions = [];
  List<Map<String, dynamic>> _chatHistory = [];
  double _progress = 0.0;
  int _questionNumber = 1;
  int _totalQuestions = 20;
  String? _sessionId;
  bool _isLoading = false;
  String? _error;
  bool _isCompleted = false;
  String? _completionMessage;

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
        final currentPhase = ((questionNumber - 1) ~/ 5) + 1;

        setState(() {
          _progress = (progressData['progress'] ?? 0.0).toDouble();
          _questionNumber = questionNumber;
          _totalQuestions = progressData['total_questions'] ?? 20;
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

        // 現在の質問を取得するために会話を開始
        await _startConversation();

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
        _chatHistory.add({
          'type': 'question',
          'text': data['question'],
          'timestamp': DateTime.now(),
        });
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
        _chatHistory.add({
          'type': 'question',
          'text': data['question'],
          'timestamp': DateTime.now(),
        });
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
      final response = await _apiService.submitAnswer(answer);
      final data = response['data'];

      if (data['phase'] == 'question') {
        final newQuestionNumber = data['question_number'] ?? 1;
        final newPhase = ((newQuestionNumber - 1) ~/ 5) + 1;

        // Check if we need to transition to a new phase (every 5 questions)
        if (newPhase > _currentPhase) {
          // Clear history when entering a new phase
          setState(() {
            _chatHistory.clear();
            _currentPhase = newPhase;
          });

          // Show phase transition message
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Phase $_currentPhase開始 (質問 ${(newPhase-1)*5 + 1}-${newPhase*5})'),
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
          _totalQuestions = data['total_questions'] ?? 20;
          _isLoading = false;
          _chatHistory.add({
            'type': 'question',
            'text': data['question'],
            'timestamp': DateTime.now(),
          });
        });

        // デバッグ用ログ
        debugPrint('Progress updated: $_progress, question: $_questionNumber/$_totalQuestions, Phase: $_currentPhase');
        debugPrint('Backend data: $data');
        debugPrint('Browser Console: Progress updated: $_progress, question: $_questionNumber/$_totalQuestions, Phase: $_currentPhase');
        debugPrint('Browser Console: Backend data: $data');

        // プログレスバーアニメーションを更新
        _progressAnimController.animateTo(_progress);

        // 明示的にプログレス情報を再取得して更新
        await _updateProgress();

        await _getOptions();
        _scrollToBottom();
      } else if (data['phase'] == 'diagnosis') {
        setState(() {
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
  Future<void> _updateProgress() async {
    try {
      final progressResponse = await _apiService.getProgress();
      final progressData = progressResponse['data'];

      setState(() {
        _progress = (progressData['progress'] ?? 0.0).toDouble();
        _questionNumber = progressData['question_number'] ?? 1;
        _totalQuestions = progressData['total_questions'] ?? 20;
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

  // 会話履歴を復元
  Future<void> _restoreConversationHistory() async {
    try {
      final historyResponse = await _apiService.getConversationHistory();
      final historyData = historyResponse['data'];
      final history = historyData['history'] as List<dynamic>;

      // Filter history to only show messages from current phase
      final phaseStartIndex = (_currentPhase - 1) * 5;
      final phaseEndIndex = _currentPhase * 5;

      // Only show conversations for current phase questions
      final filteredHistory = history.where((msg) {
        // For question-type messages, check if they belong to current phase
        if (msg['type'] == 'question') {
          // Estimate question number based on position in history
          final questionIndex = history.where((h) => h['type'] == 'question').toList().indexOf(msg);
          return questionIndex >= phaseStartIndex && questionIndex < phaseEndIndex;
        }
        // For answer-type messages, include if there's a corresponding question in this phase
        return true; // Simplified: include all answers for now
      }).toList();

      setState(() {
        _chatHistory = filteredHistory.map((msg) => {
          'type': msg['type'],
          'text': msg['text'],
          'timestamp': DateTime.now(), // Use current time for restored messages
        }).toList();
      });

      // チャットの最下部にスクロール
      _scrollToBottom();
    } catch (e) {
      debugPrint('Failed to restore conversation history: $e');
      // 履歴復元に失敗してもエラーにはせず、空の履歴で続行
      setState(() {
        _chatHistory = [];
      });
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
              child: _isCompleted ? _buildCompletionView() : _buildChatView(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSimpleAppBar() {
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
          Container(
            padding: const EdgeInsets.all(8),
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
          const SizedBox(width: 12),
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
                Text(
                  'あなたの性格を分析します',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.black54,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.black54, size: 24),
            onPressed: _signOut,
          ),
        ],
      ),
    );
  }

  Widget _buildChatView() {
    return Column(
      children: [
        // 進捗バー（コンパクト版）
        _buildCompactProgressBar(),

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

                // 回答オプション
                if (_currentQuestion != null && _currentOptions.isNotEmpty && !_isLoading)
                  _buildOptions(),

                // 入力エリア
                if (_currentQuestion != null && !_isLoading)
                  _buildInputArea(),

                // ローディング
                if (_isLoading) _buildLoading(),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCompactProgressBar() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(16),
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

  Widget _buildChatBubble(Map<String, dynamic> message, int index) {
    final isQuestion = message['type'] == 'question';
    final text = message['text'] as String;

    return AnimatedContainer(
      duration: Duration(milliseconds: 300 + (index * 100)),
      curve: Curves.easeOut,
      margin: const EdgeInsets.only(bottom: 16),
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
                    fontSize: 17,
                    height: 1.4,
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
                  fontSize: 17,
                  height: 1.4,
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
    );
  }

  Widget _buildOptions() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '選択肢から選ぶ',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 12),
          ..._currentOptions.asMap().entries.map((entry) {
            final index = entry.key;
            final option = entry.value;

            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              child: InkWell(
                onTap: () => _submitAnswer(option),
                borderRadius: BorderRadius.circular(8),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
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
                            String.fromCharCode(65 + index), // A, B, C...
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          option,
                          style: const TextStyle(
                            fontSize: 16,
                            height: 1.4,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                      const Icon(
                        Icons.arrow_forward_ios,
                        size: 14,
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

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(16),
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
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 8),
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
    return Container(
      color: Colors.white,
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(32),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.1),
                      blurRadius: 20,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.black,
                        borderRadius: BorderRadius.circular(32),
                      ),
                      child: const Icon(
                        Icons.psychology,
                        size: 48,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 24),
                    const Text(
                      '診断完了！',
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 16),
                    if (_completionMessage != null)
                      Text(
                        _completionMessage!,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 18,
                          height: 1.6,
                          color: Colors.black87,
                        ),
                      ),
                    const SizedBox(height: 32),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {
                          setState(() {
                            _isCompleted = false;
                            _currentQuestion = null;
                            _currentOptions = [];
                            _chatHistory = [];
                            _progress = 0.0;
                            _questionNumber = 1;
                            _sessionId = null;
                          });
                          _bubbleAnimController.reset();
                          _progressAnimController.reset();
                          // 新しい会話を強制的に開始（既存セッションを無視）
                          _startNewConversation();
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.black,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        child: const Text(
                          'もう一度診断する',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
