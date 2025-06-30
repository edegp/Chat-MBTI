import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend/services/api_service.dart';
import 'package:firebase_auth/firebase_auth.dart';

class ResultPage extends StatelessWidget {
  final List<JudgeAndReport> reports;
  final List<Future<JudgeAndReport>> reportFutures;
  final VoidCallback? onRestartDiagnosis; // 診断を再開するためのコールバック
  const ResultPage({
    Key? key,
    required this.reports,
    required this.reportFutures,
    this.onRestartDiagnosis,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return _ResultPageContent(
      reports: reports,
      reportFutures: reportFutures,
      onRestartDiagnosis: onRestartDiagnosis,
    );
  }
}

class _ResultPageContent extends StatefulWidget {
  final VoidCallback? onRestartDiagnosis;
  final List<JudgeAndReport> reports;
  final List<Future<JudgeAndReport>> reportFutures;
  const _ResultPageContent({
    Key? key,
    this.onRestartDiagnosis,
    required this.reports,
    required this.reportFutures,
  }) : super(key: key);

  @override
  State<_ResultPageContent> createState() => _ResultPageContentState();
}

class _ResultPageContentState extends State<_ResultPageContent> {
  // ...existing code...
  void _resetReports() {
    setState(() {
      _reports.clear();
      _allReportsLoaded = false;
      _predLabels.clear();
      _selectedMbtiType = null;
      _feedbackSent = false;
    });
  }

  final List<int> _elementIds = [1, 2, 3, 4];
  List<JudgeAndReport> get _reports => widget.reports;
  List<Future<JudgeAndReport>> get reportFutures => widget.reportFutures;
  late StreamSubscription _streamSubscription;
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _feedbackTextController = TextEditingController();
  final Map<String, List<String>> _elementToLabels = const {
    'energy': ['I', 'E'],
    'mind': ['N', 'S'],
    'nature': ['F', 'T'],
    'tactics': ['J', 'P'],
  };
  final List<String> _mbtiTypeOptions = const [
    'INTJ  建築家',
    'INTP  論理学者',
    'ENTJ  指揮官',
    'ENTP  討論者',
    'INFJ  提唱者',
    'INFP  仲介者',
    'ENFJ  主人公',
    'ENFP  運動家',
    'ISTJ  管理者',
    'ISFJ  擁護者',
    'ESTJ  幹部',
    'ESFJ  領事',
    'ISTP  巨匠',
    'ISFP  冒険家',
    'ESTP  起業家',
    'ESFP  エンターテイナー',
  ];
  final List<String> reportHeadings = const [
    "エネルギーの方向",
    "ものの見方",
    "判断の仕方",
    "外界との接し方",
  ];
  bool _feedbackSent = false;
  bool _hasSentFeedback = false;
  bool _checkingFeedback = true;
  final ApiService _apiService = ApiService();
  bool _allReportsLoaded = false;
  final List<String> _predLabels = [];
  String? _selectedMbtiType;
  @override
  void initState() {
    super.initState();
    _restoreReportsIfNeeded();
    _checkFeedbackStatus();
  }

  Future<void> _checkFeedbackStatus() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      setState(() {
        _hasSentFeedback = false;
        _checkingFeedback = false;
      });
      return;
    }
    final userId = user.uid;
    try {
      final sent = await _apiService.hasSentFeedback(userId);
      setState(() {
        _hasSentFeedback = sent;
        _feedbackSent = sent;
        _checkingFeedback = false;
      });
    } catch (e) {
      setState(() {
        _hasSentFeedback = false;
        _checkingFeedback = false;
      });
    }
  }

  Future<void> _restoreReportsIfNeeded() async {
    if (_reports.isNotEmpty || _allReportsLoaded) return;
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;
    final userId = user.uid;
    List<JudgeAndReport> restored = [];
    for (int i = 0; i < _elementIds.length; i++) {
      final report = await _apiService.restoreReport(
        userId: userId,
        elementId: _elementIds[i],
      );
      if (report != null) {
        restored.add(report);
      }
    }
    if (restored.isNotEmpty) {
      setState(() {
        _reports.clear();
        _reports.addAll(restored);
        _predLabels.clear();
        _predLabels.addAll(restored.map((r) => r.pred_label));
        _allReportsLoaded = true;
      });
    }
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  void dispose() {
    _streamSubscription.cancel();
    _scrollController.dispose();
    _feedbackTextController.dispose();
    super.dispose();
  }

  Widget _buildFinalResultBanner() {
    String finalType = _predLabels.join();
    if (finalType.isEmpty && _reports.isNotEmpty) {
      finalType = _reports.map((r) => r.pred_label).join();
    }
    final String displayText = _mbtiTypeOptions.firstWhere(
      (option) => option.startsWith(finalType),
      orElse: () => finalType,
    );
    return Container(
      margin: const EdgeInsets.only(bottom: 24.0),
      padding: const EdgeInsets.all(16.0),
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12.0),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: RichText(
        textAlign: TextAlign.center,
        text: TextSpan(
          style: const TextStyle(
            fontSize: 20,
            color: Colors.black87,
            height: 1.5,
          ),
          children: <TextSpan>[
            const TextSpan(
              text: 'あなたの性格タイプは\n',
              style: TextStyle(
                color: Colors.black54,
                fontWeight: FontWeight.w500,
              ),
            ),
            TextSpan(
              text: finalType,
              style: const TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.black,
              ),
            ),
            const TextSpan(
              text: '\nであると考えられます',
              style: TextStyle(
                color: Colors.black54,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeedbackSection(BuildContext context) {
    return _FeedbackSection(
      mbtiTypeOptions: _mbtiTypeOptions,
      selectedMbtiType: _selectedMbtiType,
      feedbackTextController: _feedbackTextController,
      apiService: _apiService,
      onMbtiTypeChanged: (type) => setState(() => _selectedMbtiType = type),
      onFeedbackSent: () => setState(() => _feedbackSent = true),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAF9F6),
      appBar: AppBar(
        title: const Text('診断結果'),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 1,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    return ListView(
      controller: _scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        if (_allReportsLoaded) _buildFinalResultBanner(),
        for (int i = 0; i < 4; i++) ...[
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  reportHeadings.length > i ? reportHeadings[i] : '診断レポート',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                    color: Colors.black,
                  ),
                ),
                const SizedBox(height: 8),
                if (i < _reports.length)
                  MarkdownBody(data: _reports[i].report)
                else
                  const Center(
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: 24),
                      child: CircularProgressIndicator(),
                    ),
                  ),
              ],
            ),
          ),
        ],
        // --- フィードバックはレポートのロード状況に関係なく表示 ---
        _checkingFeedback
            ? const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: CircularProgressIndicator(),
              ),
            )
            : (!_feedbackSent
                ? _buildFeedbackSection(context)
                : Column(
                  children: [
                    const Center(
                      child: Text(
                        'ご協力ありがとうございました！',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.deepPurple,
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.black,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          textStyle: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.2,
                          ),
                          elevation: 2,
                        ),
                        onPressed: () {
                          _resetReports();
                          widget.onRestartDiagnosis?.call();
                          Navigator.of(context).pop(true);
                        },
                        child: const Text(
                          'もう一度診断する',
                          style: TextStyle(color: Colors.white),
                        ),
                      ),
                    ),
                  ],
                )),
      ],
    );
  }
}

class _FeedbackSection extends StatefulWidget {
  final List<String> mbtiTypeOptions;
  final String? selectedMbtiType;
  final TextEditingController feedbackTextController;
  final ApiService apiService;
  final ValueChanged<String?> onMbtiTypeChanged;
  final VoidCallback onFeedbackSent;

  const _FeedbackSection({
    required this.mbtiTypeOptions,
    required this.selectedMbtiType,
    required this.feedbackTextController,
    required this.apiService,
    required this.onMbtiTypeChanged,
    required this.onFeedbackSent,
  });

  @override
  State<_FeedbackSection> createState() => _FeedbackSectionState();
}

class _FeedbackSectionState extends State<_FeedbackSection> {
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'データ収集にご協力お願いします！',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: widget.selectedMbtiType,
            hint: const Text('性格タイプを選択'),
            isExpanded: true,
            decoration: const InputDecoration(border: OutlineInputBorder()),
            items:
                widget.mbtiTypeOptions.map((String value) {
                  return DropdownMenuItem<String>(
                    value: value,
                    child: Text(value, overflow: TextOverflow.ellipsis),
                  );
                }).toList(),
            onChanged: (String? newValue) {
              widget.onMbtiTypeChanged(newValue);
            },
          ),
          const SizedBox(height: 16),
          TextField(
            controller: widget.feedbackTextController,
            decoration: const InputDecoration(
              hintText: 'ご意見・ご感想など',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.black, // チャット画面と同じ黒色
                foregroundColor: Colors.white, // 文字色を白
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                textStyle: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.2,
                ),
                elevation: 2,
              ),
              onPressed: () async {
                final selectedType = widget.selectedMbtiType ?? '未選択';
                final feedbackText = widget.feedbackTextController.text;

                String userId = '';
                try {
                  userId = FirebaseAuth.instance.currentUser?.uid ?? '';
                } catch (_) {
                  userId = '';
                }

                final timestamp = DateTime.now().millisecondsSinceEpoch;
                final sanitizedType = selectedType.replaceAll(
                  RegExp(r'\\s+'),
                  '',
                );
                final fileName = '${userId}_${timestamp}_$sanitizedType.txt';

                bool uploadSuccess = false;
                String uploadError = '';
                try {
                  final url = await widget.apiService
                      .uploadTextToFirebaseStorage(feedbackText, fileName);
                  uploadSuccess = url != null;
                } catch (e) {
                  uploadError = e.toString();
                }

                showDialog(
                  context: context,
                  builder:
                      (context) => AlertDialog(
                        title: Text(uploadSuccess ? 'フィードバック送信' : '送信エラー'),
                        content:
                            uploadSuccess
                                ? Column(
                                  mainAxisSize: MainAxisSize.min,
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text('ご協力ありがとうございます！'),
                                    const SizedBox(height: 12),
                                    Text('選択タイプ: $selectedType'),
                                    const SizedBox(height: 8),
                                    const Text('自由記述:'),
                                    Text(feedbackText, softWrap: true),
                                  ],
                                )
                                : Text('送信に失敗しました: $uploadError'),
                        actions: [
                          TextButton(
                            child: const Text(
                              'OK',
                              style: TextStyle(color: Colors.black),
                            ),
                            onPressed: () {
                              Navigator.of(context).pop();
                              if (uploadSuccess) {
                                widget.onFeedbackSent();
                              }
                            },
                          ),
                        ],
                      ),
                );
              },
              child: const Text(
                'フィードバックを送信',
                style: TextStyle(color: Colors.white),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
