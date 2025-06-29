import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:frontend/services/api_service.dart';
import 'package:firebase_auth/firebase_auth.dart';

class ResultPage extends StatelessWidget {
  const ResultPage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return _ResultPageContent();
  }
}

class _ResultPageContent extends StatefulWidget {
  final VoidCallback? onRestartDiagnosis;
  const _ResultPageContent({Key? key, this.onRestartDiagnosis}) : super(key: key);

  @override
  _ResultPageContentState createState() => _ResultPageContentState();
}

class _ResultPageContentState extends State<_ResultPageContent> {
  late StreamSubscription _streamSubscription;
  final List<JudgeAndReport> _receivedReports = [];
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

  Stream<String> generateJsonStream() async* {
  final jsonParts = [
    { "element": "energy", "report": "## 性格診断レポート：内向型(I)\n\n会話履歴を分析した結果、あなたはMBTIにおける内向型(I)である可能性が高いと判断しました。その理由は以下の通りです。\n\n## 1. 個人的な活動によるリフレッシュ\n\n  あなたは、知らない町を散歩したり、カフェで読書をしたりするなど、一人で過ごす時間をリフレッシュ方法として挙げています。これは、内向型の人が外部からの刺激よりも、自分の内面世界に集中することでエネルギーを充電する傾向があることを示唆しています。\n\n## 2. 条件付きの社交性\n\n  複数人でリフレッシュできることとして「お酒を飲みながら語る」ことを挙げていますが、「孤独を感じた時」という条件付きです。これは、内向型の人が社交的な活動を完全に避けるわけではないものの、特定の状況や必要性に基づいて選択的に関わる傾向があることを示しています。\n\n## 3. 受動的なコミュニケーションスタイル\n\n  複数人でご飯を食べる時の役割として「聞き役が多い」と答えており、積極的に会話をリードするタイプではないことが示唆されます。内向型の人は、発言する前に考えを深め、聞き手に回ることが多い傾向があります。", "gemma_judge": "[/judge]\n\n[reason]:一人でカフェで読書をするなど、一人で過ごす時間を好む傾向がある\n初対面の人と積極的に交流するよりも、すでに知っている人と過ごすことを好む\n新しいことを学ぶ際、最終的に何をしたいかを決め、そこから着実に進めていく\nカフェでの読書など、穏やかな環境で自分と向き合うことでエネルギーをチャージする\n[judge]:I[/judge]", "gemma_success": false, "pred_label": "I"},
    { "element": "mind", "report": "## MBTI：直観型(N)の可能性が高い理由\n\n会話履歴から判断すると、あなたはMBTIの直観型(N)の傾向が強いと考えられます。その理由を以下に示します。\n\n## 1. 趣味について話すことを好む\n\n趣味について話すことを好むという点は、直観型(N)の特徴である「可能性」や「未来」への興味と関連しています。直観型は、現実の具体的な事柄よりも、アイデアや概念、そしてそれらがもたらす可能性について語ることを好む傾向があります。あなたの「趣味の時間を楽しんでいます」という発言や、その内容に関する質問への回答から、具体的な行動よりも、その趣味がもたらす経験や感情、そこから広がる可能性に重きを置いている様子が伺えます。\n\n## 2. 空想を広げることを好む\n\n空想を広げることを好む点は、まさに直観型(N)を特徴づける行動です。直観型は、五感で捉えられる情報よりも、頭の中で作り上げたイメージやインスピレーションを重視します。あなたの「自分の空想を広げられるとき」に一人で過ごす時間を良いと感じるという発言は、この直観型の傾向を強く示唆しています。\n\n## 3. 具体的な説明をしない「間」を持った抽象度の高い話をする\n\n具体的な説明を避け、抽象度の高い話をする傾向は、直観型(N)の特徴の一つです。直観型は、細部にこだわるよりも全体像を把握することを重視し、具体的な事柄よりも概念的な理解を優先します。あなたの回答は、具体的な行動や状況に関する質問に対して、やや抽象的な表現にとどまっている部分があります。これは、詳細な情報よりも、背後にある概念やアイデアを重視する直観型の思考パターンを反映している可能性があります。", "gemma_judge": "[reason]:趣味について話すことを好む\n空想を広げることを好む\n具体的な説明をしない「間」を持った抽象度の高い話をする\n[judge]:N", "gemma_success": true, "pred_label": "N"},
    { "element": "nature", "report": "## MBTI診断結果：感情型(F)\n\n会話履歴から判断すると、あなたはMBTIにおける感情型(F)である可能性が高いです。以下の理由から、そのように判断しました。\n\n## 1. 意見の言い換えが難しい状況で感情に配慮する\n\nあなたは、意見の言い換えが難しいと感じる状況でも、相手の感情に配慮したコミュニケーションを心がけているようです。これは、論理的な正しさよりも、相手の気持ちを尊重する感情型(F)の特徴を示しています。\n\n## 2. 相手の立場に立って考える\n\nあなたは、相手の立場に立って物事を考えることを重視しています。これは、感情型(F)が共感性や調和を大切にする性質と一致します。相手の気持ちを理解しようと努める姿勢は、感情型(F)の重要な特徴です。\n\n## 3. 相手の気持ちを害する可能性を考慮する\n\nあなたは、発言や行動が相手の気持ちを害する可能性を常に考慮しているようです。これは、感情型(F)が人間関係を円滑に保つことを重視する傾向の表れです。相手の気持ちを第一に考えるあなたの姿勢は、感情型(F)の典型的な特徴と言えるでしょう。", "gemma_judge": "[reason]:意見の言い換えが難しいと感じる状況で、相手の感情に配慮して、感情的なアプローチを取る\n相手の立場に立って考える\n相手の気持ちを害する可能性を考慮する\n[judge]:F", "gemma_success": true ,"pred_label": "F"},
    { "element": "tactics", "report": "性格診断の結果から、あなたはMBTIにおける **判断型(J)** である可能性が高いと判断しました。以下にその理由を詳しく説明します。\n\n## 1. 将来の自分を納得させられるか\n\n  大きな買い物をするときの判断基準として「将来の自分を納得させられるか」という点を挙げていることから、計画性や将来を見据えた思考が強いことが伺えます。判断型(J)は、明確な目標を持ち、計画的に物事を進めることを好む傾向があります。将来のリスクや後悔を考慮し、論理的に判断を下す姿勢は、判断型(J)の特徴と一致します。\n\n## 2. 明確な判断基準や論理\n\n  「将来の自分を納得させられるか」という基準は、一見抽象的に見えますが、あなたの中には明確な判断基準や論理が存在していると考えられます。判断型(J)は、自身の価値観や原則に基づいて判断を下すことが多く、そのため、一貫性のある行動を取ることが特徴です。\n\n## 3. 責任や完了に対する意識\n\n  「将来の自分を納得させられるか」という言葉には、将来に対する責任感や、物事を最後までやり遂げたいという完了欲求が含まれていると考えられます。判断型(J)は、責任感が強く、計画したことを最後までやり遂げることに喜びを感じる傾向があります。将来を見据えた判断基準を持つことは、責任感の表れと言えるでしょう。", "gemma_judge": "[reason]:将来の自分を納得させられるかという発言は、計画や構造を重視する判断型に多く見られる\n明確な判断基準や論理\n責任や完了に対する意識\n[judge]:J", "gemma_success": true ,"pred_label": "J"}
  ];

  for (final part in jsonParts) {
    await Future.delayed(const Duration(milliseconds: 1500));
    final jsonString = jsonEncode(part);
    yield jsonString;
  }
}


  final ApiService _apiService = ApiService();
  // late final Stream<JudgeAndReport> reportStream = _apiService
  //     .fetchReportStreamFromApi()
  //     .map((jsonString) {
  //       final decodedJson = jsonDecode(jsonString);
  //       return JudgeAndReport.fromJson(decodedJson);
  //     });
  late final Stream<JudgeAndReport> reportStream = generateJsonStream().map((jsonString) => JudgeAndReport.fromJson(jsonDecode(jsonString)));

  bool _allReportsLoaded = false;
  final List<String> _predLabels = [];
  String? _selectedMbtiType;

  @override
  void initState() {
    super.initState();
    _listenToStream();
  }

  void _listenToStream() {
    _streamSubscription = reportStream.listen(
      (newReport) {
        if (mounted) {
          setState(() {
            _receivedReports.add(newReport);
            if (newReport.pred_label.isNotEmpty) {
              _predLabels.add(newReport.pred_label);
            }
            if (_receivedReports.length >= 4) {
              _allReportsLoaded = true;
            }
          });
        }
      },
      onDone: () {
        if (mounted && !_allReportsLoaded) {
          setState(() {
            _allReportsLoaded = true;
          });
          // 完了したら一番下までスクロール
          Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
        }
      },
    );
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
    final String finalType = _predLabels.join();
    final String displayText = _mbtiTypeOptions.firstWhere(
      (option) => option.startsWith(finalType),
      orElse: () => finalType,
    );

    return Container(
      margin: const EdgeInsets.only(bottom: 24.0),
      padding: const EdgeInsets.all(16.0),
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.deepPurple.shade50,
        borderRadius: BorderRadius.circular(8.0),
      ),
      child: RichText(
        textAlign: TextAlign.center,
        text: TextSpan(
          style: TextStyle(fontSize: 20, color: Colors.grey[800], height: 1.5),
          children: <TextSpan>[
            const TextSpan(text: 'あなたの性格タイプは\n'),
            TextSpan(
              text: finalType,
              style: const TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.deepPurple,
              ),
            ),
            const TextSpan(text: '\nであると考えられます'),
          ],
        ),
      ),
    );
  }

  // 正解ラベルの収集＆フィードバックのウィジット
  // 送信ボタンを押すとデータがGCSに送信されるようにしたい
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
    // 必ずWidgetを返すよう修正
    return Scaffold(
      appBar: AppBar(title: const Text('診断結果')),
      body: _buildBody(),
    );
  }
  Widget _buildBody() {
    if (_receivedReports.isEmpty) {
      return const Center(child: Text("診断結果を生成中です..."));
    }

    return ListView(
      controller: _scrollController,
      padding: const EdgeInsets.all(16),
      children: [
        if (_allReportsLoaded) _buildFinalResultBanner(),
        for (int i = 0; i < _receivedReports.length; i++) ...[
          Text(
            reportHeadings.length > i ? reportHeadings[i] : '診断レポート',
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.deepPurple),
          ),
          const SizedBox(height: 8),
          MarkdownBody(data: _receivedReports[i].report),
          const SizedBox(height: 24),
        ],
        if (_allReportsLoaded && !_feedbackSent)
          _buildFeedbackSection(context),
        if (_allReportsLoaded && _feedbackSent) ...[
          const Center(
            child: Text(
              'ご協力ありがとうございました！',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.deepPurple),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.deepPurple,
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(vertical: 16),
              ),
              onPressed: () {
                Navigator.of(context).pop(true);
              },
              child: const Text('もう一度診断する'),
            ),
          ),
        ],
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
            items: widget.mbtiTypeOptions.map((String value) {
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
                backgroundColor: Colors.deepPurple,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
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
                final sanitizedType = selectedType.replaceAll(RegExp(r'\\s+'), '');
                final fileName = '${userId}_${timestamp}_$sanitizedType.txt';

                bool uploadSuccess = false;
                String uploadError = '';
                try {
                  final url = await widget.apiService.uploadTextToFirebaseStorage(feedbackText, fileName);
                  uploadSuccess = url != null;
                } catch (e) {
                  uploadError = e.toString();
                }

                showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: Text(uploadSuccess ? 'フィードバック送信' : '送信エラー'),
                    content: uploadSuccess
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
                        child: const Text('OK'),
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
              child: const Text('フィードバックを送信'),
            ),
          ),
        ],
      ),
    );
  }
}
