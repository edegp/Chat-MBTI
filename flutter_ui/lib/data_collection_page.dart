// ignore_for_file: constant_identifier_names, prefer_final_fields, avoid_print, use_build_context_synchronously, non_constant_identifier_names, unused_local_variable

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:csv/csv.dart';
import 'package:universal_html/html.dart' as html;
import 'services/data_collection_api_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/gestures.dart';

class DataCollectionPage extends StatefulWidget {
  const DataCollectionPage({super.key});

  @override
  State<DataCollectionPage> createState() => _DataCollectionPageState();
}

class _DataCollectionPageState extends State<DataCollectionPage> {
  final DataCollectionApiService _apiService = DataCollectionApiService();
  final TextEditingController _textController = TextEditingController();
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _personalityController = TextEditingController();
  // List of 16 MBTI personality codes
  static const List<String> _personalityTypes = [
    'ISTJ','ISFJ','INFJ','INTJ',
    'ISTP','ISFP','INFP','INTP',
    'ESTP','ESFP','ENFP','ENTP',
    'ESTJ','ESFJ','ENFJ','ENTJ'
  ];
  String? _personalityCode;

  static const Map<String, String> _elementNames = {
    'ISTJ': '管理者',
    'ISFJ': '守護者',
    'INFJ': '提唱者',
    'INTJ': '建築家',
    'ISTP': '職人',
    'ISFP': '芸術家',
    'INFP': '理想家',
    'INTP': '論理学者',
    'ESTP': '起業家',
    'ESFP': 'エンターテイナー',
    'ENFP': '活動家',
    'ENTP': '討論者',
    'ESTJ': '管理職',
    'ESFJ': '提供者',
    'ENFJ': '教師',
    'ENTJ': '指導者'
  };

  // Data collection parameters - 4 MBTI elements with 10 questions each, repeated 5 times
  static const int QUESTIONS_PER_ELEMENT = 10; // 10 questions per MBTI element
  static const int TOTAL_ELEMENTS = 4;         // 4 MBTI elements (Energy, Mind, Nature, Tactics)
  static const int CYCLES_PER_COLLECTION = 5;  // Repeat 5 times
  static const int TOTAL_PHASES = TOTAL_ELEMENTS * CYCLES_PER_COLLECTION; // 20 phases total

  // Current state
  int _currentPhase = 1;
  int _currentQuestionInPhase = 1;
  String? _currentQuestion;
  List<String> _currentOptions = [];
  String? _sessionId;
  bool _isLoading = false;
  bool _isCollectionInProgress = false;
  String? _error;
  String? _participantName;

  // Data storage
  List<Map<String, dynamic>> _collectedData = [];
  List<Map<String, dynamic>> _currentSessionData = [];
  List<List<String>> _optionsHistory = [];  // track options per question for back navigation
  // History per phase for session data and options, to support back navigation across phase boundaries
  List<List<Map<String, dynamic>>> _phaseSessionHistory = [];
  List<List<List<String>>> _phaseOptionsHistory = [];

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
    });

    await _startNewPhase();
  }

  // MBTI element_id rotation: 1=energy, 2=mind, 3=nature, 4=tactics
  int _getCurrentElementId() {
    return ((_currentPhase - 1) % TOTAL_ELEMENTS) + 1;
  }

  Future<void> _startNewPhase() async {
    setState(() {
      _isLoading = true;
      _currentQuestionInPhase = 1;
      _currentSessionData.clear();
      _optionsHistory.clear();
    });

    try {
      // Calculate element_id for this phase
      final elementId = _getCurrentElementId();
      // Start new conversation for this phase with element_id
      final response = await _apiService.startNewConversation(elementId: elementId);

      setState(() {
        _currentQuestion = response['data']['question'];
        _sessionId = response['data']['session_id'];
        _isLoading = false;
      });

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
      final options = List<String>.from(response['data']['options'] ?? []);
      setState(() {
        _currentOptions = options;
        _optionsHistory.add(options);
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
    });

    try {
      // Record the Q&A pair
      final newEntry = {
        'participant_name': _participantName,
        'phase': _currentPhase,
        'element_type': _getCurrentElementType(),
        'cycle_number': _getCurrentCycle(),
        'question_number_in_phase': _currentQuestionInPhase,
        'question': _currentQuestion,
        'answer': answer,
        'timestamp': DateTime.now().toIso8601String(),
        'session_id': _sessionId,
      };

      _currentSessionData.add(newEntry);

      print('DEBUG: Added entry to _currentSessionData: $newEntry');
      print('DEBUG: _currentSessionData now has ${_currentSessionData.length} entries');

      if (_currentQuestionInPhase < QUESTIONS_PER_ELEMENT) {
        // Continue with next question in current element
        final response = await _apiService.submitAnswer(answer);

        setState(() {
          _currentQuestion = response['data']['question'];
          _currentQuestionInPhase++;
          _isLoading = false;
        });

        await _getOptions();
      } else {
        // Element/Phase completed
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
    // Download CSV for the completed phase BEFORE clearing data
    _downloadPhaseCSV(_currentPhase);

    // --- GCSアップロード: フェーズごとにアップロード ---
    await _uploadPhaseCsvToGcs(_currentPhase);

    // Add current session data to collected data
    _collectedData.addAll(_currentSessionData);

    // Save completed phase session data and options history for back navigation
    _phaseSessionHistory.add(List<Map<String, dynamic>>.from(_currentSessionData));
    _phaseOptionsHistory.add(List<List<String>>.from(_optionsHistory));

    if (_currentPhase < TOTAL_PHASES) {
      // Move to next phase
      setState(() {
        _currentPhase++;
      });

      // Show phase completion message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('フェーズ ${_currentPhase - 1} 完了！CSVダウンロード開始。フェーズ $_currentPhase を開始します...'),
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
    // 全フェーズ終了時に自動でGCSへアップロード
    await _uploadCsvToGcs();
    await _clearProgressPrefs();

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('データ収集が完了しました！CSVファイルをダウンロードできます。'),
        backgroundColor: Colors.green,
        duration: Duration(seconds: 3),
      ),
    );
  }

  void _downloadCSV() {
    if (_collectedData.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('ダウンロードするデータがありません'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    // Prepare CSV data
    List<List<dynamic>> csvData = [
      // Header including personality code
      ['Participant Name', 'Personality Code', 'Phase', 'Element Type', 'Cycle Number', 'Question Number', 'Question', 'Answer', 'Timestamp', 'Session ID']
    ];

    // Add data rows
    for (var item in _collectedData) {
      final phase = item['phase'] as int;
      final idx = (phase - 1) % TOTAL_ELEMENTS;
      final codeLetter = (_personalityCode != null && _personalityCode!.length > idx)
          ? _personalityCode![idx]
          : '';
      csvData.add([
        item['participant_name'],
        codeLetter,
        item['phase'],
        item['element_type'],
        item['cycle_number'],
        item['question_number_in_phase'],
        item['question'],
        item['answer'],
        item['timestamp'],
        item['session_id'],
      ]);
    }

    // Convert to CSV string
    String csvString = const ListToCsvConverter().convert(csvData);

    // Create and download file
    final bytes = utf8.encode(csvString);
    final blob = html.Blob([bytes], 'text/csv;charset=utf-8');
    final url = html.Url.createObjectUrlFromBlob(blob);
    final anchor = html.document.createElement('a') as html.AnchorElement
      ..href = url
      ..style.display = 'none'
      ..download = 'mbti_data_collection_${_participantName ?? 'anonymous'}_all_${DateTime.now().toIso8601String().replaceAll(RegExp(r'[:\-T\.]'), '').substring(0, 15)}.csv';
    html.document.body?.children.add(anchor);
    anchor.click();
    html.document.body?.children.remove(anchor);
    html.Url.revokeObjectUrl(url);

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('CSVファイルをダウンロードしました'),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _downloadPhaseCSV(int phaseNumber) {
    // Use current session data directly since it contains data for the current phase
    final phaseData = List<Map<String, dynamic>>.from(_currentSessionData);

    print('DEBUG: Downloading CSV for phase $phaseNumber');
    print('DEBUG: _currentSessionData length: ${_currentSessionData.length}');
    print('DEBUG: phaseData length: ${phaseData.length}');
    print('DEBUG: _currentSessionData content: $_currentSessionData');

    if (phaseData.isEmpty) {
      print('WARNING: No data found for phase $phaseNumber');
      return;
    }

    // Prepare CSV data for this phase
    List<List<dynamic>> csvData = [
      // Header including personality code
      ['Participant Name', 'Personality Code', 'Phase', 'Element Type', 'Cycle Number', 'Question Number', 'Question', 'Answer', 'Timestamp', 'Session ID']
    ];

    final idx = (_currentPhase - 1) % TOTAL_ELEMENTS;
    final codeLetter = (_personalityCode != null && _personalityCode!.length > idx)
        ? _personalityCode![idx]
        : '';
    // Add data rows
    for (var item in phaseData) {
      csvData.add([
        item['participant_name'],
        codeLetter,
        item['phase'],
        item['element_type'],
        item['cycle_number'],
        item['question_number_in_phase'],
        item['question'],
        item['answer'],
        item['timestamp'],
        item['session_id'],
      ]);
    }

    // Convert to CSV string
    String csvString = const ListToCsvConverter().convert(csvData);

    // Create and download file
    final bytes = utf8.encode(csvString);
    final blob = html.Blob([bytes], 'text/csv;charset=utf-8');
    final url = html.Url.createObjectUrlFromBlob(blob);
    final anchor = html.document.createElement('a') as html.AnchorElement
      ..href = url
      ..style.display = 'none'
      ..download = 'data_element${(phaseNumber - 1) % TOTAL_ELEMENTS + 1}_phase${phaseNumber}_${_participantName ?? 'anonymous'}_${DateTime.now().toIso8601String().replaceAll(RegExp(r'[:\-T\.]'), '').substring(0, 15)}.csv';
    html.document.body?.children.add(anchor);
    anchor.click();
    html.document.body?.children.remove(anchor);
    html.Url.revokeObjectUrl(url);
  }

  Future<void> _signOut() async {
    await _clearProgressPrefs();
    // For data collection page, just navigate to home instead of signing out
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/');
    }
  }

  String _getCurrentElementType() {
    final elementTypes = ['エネルギー (I/E)', '情報収集 (N/S)', '意思決定 (T/F)', '外界への態度 (J/P)'];
    final elementIndex = ((_currentPhase - 1) % TOTAL_ELEMENTS);
    return elementTypes[elementIndex];
  }

  int _getCurrentCycle() {
    return ((_currentPhase - 1) ~/ TOTAL_ELEMENTS) + 1;
  }

  Future<void> _saveProgressToPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final saveData = jsonEncode({
      'participantName': _participantName,
      'personalityCode': _personalityCode,
      'currentPhase': _currentPhase,
      'collectedData': _collectedData,
    });
    await prefs.setString('mbti_data_collection_progress', saveData);
  }

  Future<void> _restoreProgressFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final saveData = prefs.getString('mbti_data_collection_progress');
    if (saveData != null) {
      try {
        final decoded = jsonDecode(saveData);
        setState(() {
          _participantName = decoded['participantName'];
          _personalityCode = decoded['personalityCode'];
          if (_personalityCode != null) {
            _personalityController.text = _personalityCode!;
          }
          _currentPhase = decoded['currentPhase'] ?? 1;
          _collectedData = List<Map<String, dynamic>>.from(decoded['collectedData'] ?? []);
          _isCollectionInProgress = true;
        });
        // 途中から再開
        await _startNewPhase();
      } catch (e) {
        // 復元失敗時は何もしない
      }
    }
  }

  Future<void> _clearProgressPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('mbti_data_collection_progress');
  }

  // リセット確認ダイアログを表示
  Future<void> _confirmReset() async {
    final shouldReset = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('リセットしますか？'),
        content: const Text('現在の進行状況は失われます。よろしいですか？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('キャンセル'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('はい'),
          ),
        ],
      ),
    );
    if (shouldReset == true) {
      _goToStart();
    }
  }

  void _goToStart() {
    // Reset state to initial input screen
    _clearProgressPrefs();
    setState(() {
      _isCollectionInProgress = false;
      _participantName = null;
      _personalityCode = null;
      _collectedData.clear();
      _currentSessionData.clear();
      _currentPhase = 1;
      _currentQuestionInPhase = 1;
      _nameController.clear();
      _personalityController.clear();
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAF9F6),
      body: SafeArea(
        child: Column(
          children: [
            _buildAppBar(),
            Expanded(
              child: _buildMainContent(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAppBar() {
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
          if (!_isCollectionInProgress)
            IconButton(
              icon: const Icon(Icons.arrow_back, color: Colors.black54),
              onPressed: () => Navigator.pushReplacementNamed(context, '/'),
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
              onTap: _isCollectionInProgress ? _confirmReset : null,
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
            onPressed: _signOut,
          ),
        ],
      ),
    );
  }

  Widget _buildMainContent() {
    return Container(
      margin: const EdgeInsets.all(16),
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
          _buildProgressHeader(),
          Expanded(
            child: _isCollectionInProgress
                ? _buildCollectionView()
                : _buildStartView(),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressHeader() {
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
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'フェーズ $_currentPhase / $TOTAL_PHASES',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  if (_isCollectionInProgress) ...[
                    Text(
                      '${_getCurrentElementType()} (${_getCurrentCycle()}回目)',
                      style: const TextStyle(
                        fontSize: 16,
                        color: Colors.purple,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      '質問 $_currentQuestionInPhase / $QUESTIONS_PER_ELEMENT',
                      style: const TextStyle(
                        fontSize: 16,
                        color: Colors.black54,
                      ),
                    ),
                  ],
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.purple,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${_collectedData.length} / ${TOTAL_PHASES * QUESTIONS_PER_ELEMENT}',
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
            value: _collectedData.length / (TOTAL_PHASES * QUESTIONS_PER_ELEMENT),
            backgroundColor: Colors.purple[100],
            valueColor: const AlwaysStoppedAnimation<Color>(Colors.purple),
          ),
        ],
      ),
    );
  }

  Widget _buildStartView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          const SizedBox(height: 20), // Add some top spacing
          Icon(
            Icons.play_circle_outline,
            size: 64, // Reduced size
            color: Colors.purple[300],
          ),
          const SizedBox(height: 20), // Reduced spacing
          const Text(
            'データ収集を開始',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 12), // Reduced spacing

          // Data usage consent notice
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14), // Reduced padding
            decoration: BoxDecoration(
              color: Colors.blue[50],
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.blue[200]!),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.info, color: Colors.blue[600], size: 18), // Reduced size
                    const SizedBox(width: 6), // Reduced spacing
                    const Text(
                      'データ利用について',
                      style: TextStyle(
                        fontSize: 15, // Reduced font size
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10), // Reduced spacing
                const Text(
                  '収集されたデータは独自のAIの学習に使用され、AIの学習以外には使用いたしません。\n\nもしデータの削除を求める場合は、メールアドレス「 info@anful.ai , ogawa.hajime.hyr@gmail.com 」の青木・小川まで入力した名前と削除する旨をメールでお伝えください。',
                  style: TextStyle(
                    fontSize: 13, // Reduced font size
                    height: 1.4, // Reduced line height
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 10), // Reduced spacing
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10), // Reduced padding
                  decoration: BoxDecoration(
                    color: Colors.orange[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.orange[200]!),
                  ),
                  child: const Text(
                    '同意する場合のみ名前を入力して開始してください',
                    style: TextStyle(
                      fontSize: 13, // Reduced font size
                      fontWeight: FontWeight.w600,
                      color: Colors.black87,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20), // Reduced spacing

          Text(
            '• $TOTAL_PHASES フェーズ実行\n• 各フェーズ $QUESTIONS_PER_ELEMENT 問\n• 合計 ${TOTAL_PHASES * QUESTIONS_PER_ELEMENT} 問のデータを収集\n• 結果をCSVでダウンロード可能',
            style: const TextStyle(
              fontSize: 14,
              height: 1.5,
              color: Colors.black54,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          const Text(
            '※ヘッダーの「データ収集」を押すと進行状況がリセットされます',
            style: TextStyle(
              fontSize: 13,
              color: Colors.redAccent,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          // Prompt users to take personality test with clickable link
          RichText(
            textAlign: TextAlign.center,
            text: TextSpan(
              style: const TextStyle(fontSize: 14, color: Colors.black87),
              children: [
                const TextSpan(text: '性格診断がまだの方は '),
                TextSpan(
                  text: 'こちら',
                  style: const TextStyle(color: Colors.blue, decoration: TextDecoration.underline),
                  recognizer: TapGestureRecognizer()
                    ..onTap = () {
                      html.window.open(
                        'https://www.16personalities.com/ja/性格診断テスト',
                        '_blank',
                      );
                    },
                ),
                const TextSpan(text: ' から性格診断をしてください'),
              ],
            ),
          ),
          const SizedBox(height: 24),
          // Participant name input
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '参加者名',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  child: TextField(
                    controller: _nameController,
                    style: const TextStyle(fontSize: 16),
                    decoration: InputDecoration(
                      hintText: '参加者の名前を入力してください',
                      hintStyle: TextStyle(
                        color: Colors.grey[400],
                        fontSize: 16,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 16,
                      ),
                      filled: true,
                      fillColor: Colors.white,
                      prefixIcon: Icon(
                        Icons.person,
                        color: Colors.grey[400],
                      ),
                    ),
                    textInputAction: TextInputAction.done,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Personality code input
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '16性格コード',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: DropdownButtonFormField<String>(
                    value: _personalityCode,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                      filled: true,
                      fillColor: Colors.white,
                    ),
                    hint: const Text('例: INFP'),
                    items: _personalityTypes.map((type) => DropdownMenuItem<String>(
                      value: type,
                      child: Text(
                        '$type (${_elementNames[type] ?? ''})',
                        style: const TextStyle(fontSize: 16),
                      ),
                    )).toList(),
                    onChanged: (value) {
                      setState(() {
                        _personalityCode = value;
                        _personalityController.text = value ?? '';
                      });
                    },
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 20), // Reduced spacing
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _startDataCollection,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.purple,
                padding: const EdgeInsets.symmetric(vertical: 14), // Reduced padding
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: _isLoading
                  ? const SizedBox(
                      height: 18, // Reduced size
                      width: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Text(
                      'データ収集開始',
                      style: TextStyle(
                        fontSize: 16, // Reduced font size
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
            ),
          ),
          const SizedBox(height: 12), // Reduced spacing
          if (_collectedData.isNotEmpty)
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _downloadCSV,
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: Colors.purple),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text(
                      'CSVダウンロード',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.purple,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          const SizedBox(height: 20), // Add bottom spacing for scroll
        ],
      ),
    );
  }

  Widget _buildCollectionView() {
    return Column(
      children: [
        // Back button and question area
        Row(
          children: [
            IconButton(
              icon: const Icon(Icons.arrow_back),
              onPressed: _currentQuestionInPhase > 1 && !_isLoading ? _goBack : null,
            ),
            Expanded(
              child: _currentQuestion != null
                ? Text('Q$_currentQuestionInPhase: $_currentQuestion')
                : const SizedBox.shrink(),
            ),
          ],
        ),

        // Current question area
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_currentQuestion != null) ...[
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.grey[50],
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.grey[200]!),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(6),
                              decoration: BoxDecoration(
                                color: Colors.purple,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Icon(
                                Icons.psychology,
                                size: 16,
                                color: Colors.white,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Q$_currentQuestionInPhase',
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: Colors.purple,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(
                          _currentQuestion!,
                          style: const TextStyle(
                            fontSize: 18,
                            height: 1.4,
                            color: Colors.black87,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                ],

                if (_error != null) ...[
                  Container(
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
                  ),
                  const SizedBox(height: 20),
                ],

                if (_isLoading) ...[
                  const Center(
                    child: Column(
                      children: [
                        CircularProgressIndicator(
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.purple),
                        ),
                        SizedBox(height: 16),
                        Text(
                          '処理中...',
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.black54,
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

        // Answer options
        if (_currentOptions.isNotEmpty && !_isLoading) ...[
          Container(
            padding: const EdgeInsets.all(20),
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
                          color: Colors.white,
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
                                color: Colors.purple,
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
          ),
        ],

        // Custom answer input
        if (_currentQuestion != null && !_isLoading) ...[
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white,
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
                              _textController.clear();
                            }
                          },
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.purple,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: IconButton(
                        onPressed: () {
                          final text = _textController.text.trim();
                          if (text.isNotEmpty) {
                            _submitAnswer(text);
                            _textController.clear();
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
          ),
        ],
      ],
    );
  }

  // --- GCSアップロード処理 ---
  Future<void> _uploadCsvToGcs() async {
    if (_collectedData.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('アップロードするデータがありません'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }
    setState(() { _isLoading = true; });
    try {
      // Prepare CSV data
      List<List<dynamic>> csvData = [
        ['Participant Name', 'Phase', 'Element Type', 'Cycle Number', 'Question Number', 'Question', 'Answer', 'Timestamp', 'Session ID']
      ];
      for (var item in _collectedData) {
        csvData.add([
          item['participant_name'],
          item['phase'],
          item['element_type'],
          item['cycle_number'],
          item['question_number_in_phase'],
          item['question'],
          item['answer'],
          item['timestamp'],
          item['session_id'],
        ]);
      }
      String csvString = const ListToCsvConverter().convert(csvData);
      final success = await _apiService.uploadCsvToGcs(
        participantName: _participantName ?? 'anonymous',
        personalityCode: _personalityCode ?? '',
        csvContent: csvString,
      );
      setState(() { _isLoading = false; });
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('GCSへのアップロードに成功しました'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('GCSへのアップロードに失敗しました'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      setState(() { _isLoading = false; });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('アップロードエラー: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // フェーズごとのGCSアップロード処理
  Future<void> _uploadPhaseCsvToGcs(int phaseNumber) async {
    final phaseData = List<Map<String, dynamic>>.from(_currentSessionData);
    if (phaseData.isEmpty) return;
    List<List<dynamic>> csvData = [
      ['Participant Name', 'Phase', 'Element Type', 'Cycle Number', 'Question Number', 'Question', 'Answer', 'Timestamp', 'Session ID']
    ];
    int cycle_number = 0;
    for (var item in phaseData) {
      csvData.add([
        item['cycle_number'],
        item['question_number_in_phase'],
        item['question'],
        item['answer'],
        item['timestamp'],
        item['session_id'],
      ]);
    }
    String csvString = const ListToCsvConverter().convert(csvData);
    await _apiService.uploadCsvToGcs(
      participantName: _participantName ?? 'anonymous',
      personalityCode: _personalityCode ?? '',
      csvContent: csvString,
      elementId: ((phaseNumber - 1) % TOTAL_ELEMENTS) + 1, // 1-4の範囲に変換
      cycleNumber: _getCurrentCycle(),
    );
  }

  // Navigate back one question in current phase
  void _goBack() {
    if (_currentQuestionInPhase > 1) {
      // Back within the same phase
      setState(() {
        _currentSessionData.removeLast();
        _optionsHistory.removeLast();
        _currentQuestionInPhase--;
        final prevEntry = _currentSessionData.isNotEmpty ? _currentSessionData.last : null;
        if (prevEntry != null) {
          _currentQuestion = prevEntry['question'] as String?;
          _sessionId = prevEntry['session_id'] as String?;
        }
        _currentOptions = _optionsHistory.isNotEmpty ? _optionsHistory.last : [];
        _error = null;
        _isLoading = false;
      });
    } else if (_currentPhase > 1) {
      // Back to the last question of the previous phase
      setState(() {
        // Move to previous phase
        _currentPhase--;
        // Restore session data and options history for that phase
        _currentSessionData.clear();
        _currentSessionData.addAll(_phaseSessionHistory.removeLast());
        _optionsHistory.clear();
        _optionsHistory.addAll(_phaseOptionsHistory.removeLast());
        // Jump to last question in that phase
        _currentQuestionInPhase = QUESTIONS_PER_ELEMENT;
        final prevEntry = _currentSessionData.last;
        _currentQuestion = prevEntry['question'] as String?;
        _sessionId = prevEntry['session_id'] as String?;
        _currentOptions = _optionsHistory.last;
        _error = null;
        _isLoading = false;
      });
    }
  }
}
