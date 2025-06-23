import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:universal_html/html.dart' as html;
import '../constants/data_collection_constants.dart';

class StartView extends StatelessWidget {
  final TextEditingController nameController;
  final TextEditingController personalityController;
  final String? personalityCode;
  final Function(String?) onPersonalityCodeChanged;
  final VoidCallback onStartDataCollection;
  final VoidCallback? onDownloadCSV;
  final bool isLoading;
  final bool hasCollectedData;

  const StartView({
    super.key,
    required this.nameController,
    required this.personalityController,
    this.personalityCode,
    required this.onPersonalityCodeChanged,
    required this.onStartDataCollection,
    this.onDownloadCSV,
    required this.isLoading,
    required this.hasCollectedData,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          const SizedBox(height: 20),
          Icon(
            Icons.play_circle_outline,
            size: 64,
            color: Colors.purple[300],
          ),
          const SizedBox(height: 20),
          const Text(
            'データ収集を開始',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 12),

          // Data usage consent notice
          _buildConsentNotice(),
          const SizedBox(height: 20),

          // Project info
          _buildProjectInfo(),
          const SizedBox(height: 8),

          // Instructions
          _buildInstructions(),
          const SizedBox(height: 12),

          // Personality test link
          _buildPersonalityTestLink(),
          const SizedBox(height: 24),

          // Participant name input
          _buildNameInput(),
          const SizedBox(height: 16),

          // Personality code input
          _buildPersonalityCodeInput(),
          const SizedBox(height: 20),

          // Start button
          _buildStartButton(),
          const SizedBox(height: 12),

          // Download button
          if (hasCollectedData) _buildDownloadButton(),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _buildConsentNotice() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
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
              Icon(Icons.info, color: Colors.blue[600], size: 18),
              const SizedBox(width: 6),
              const Text(
                'データ利用について',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          const Text(
            '収集されたデータは独自のAIの学習に使用され、AIの学習以外には使用いたしません。\n\nもしデータの削除を求める場合は、メールアドレス「 info@anful.ai , ogawa.hajime.hyr@gmail.com 」の青木・小川まで入力した名前と削除する旨をメールでお伝えください。',
            style: TextStyle(
              fontSize: 13,
              height: 1.4,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 10),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: Colors.orange[50],
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.orange[200]!),
            ),
            child: const Text(
              '同意する場合のみ名前を入力して開始してください',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Colors.black87,
              ),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProjectInfo() {
    return Text(
      '• ${DataCollectionConstants.totalPhases} フェーズ実行\n• 各フェーズ ${DataCollectionConstants.questionsPerElement} 問\n• 合計 ${DataCollectionConstants.totalPhases * DataCollectionConstants.questionsPerElement} 問のデータを収集\n• 結果をCSVでダウンロード可能',
      style: const TextStyle(
        fontSize: 14,
        height: 1.5,
        color: Colors.black54,
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget _buildInstructions() {
    return const Text(
      '※ヘッダーの「データ収集」を押すと進行状況がリセットされます',
      style: TextStyle(
        fontSize: 13,
        color: Colors.redAccent,
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget _buildPersonalityTestLink() {
    return RichText(
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
    );
  }

  Widget _buildNameInput() {
    return Container(
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
              controller: nameController,
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
    );
  }

  Widget _buildPersonalityCodeInput() {
    return Container(
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
              value: personalityCode,
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
              items: DataCollectionConstants.personalityTypes.map((type) => DropdownMenuItem<String>(
                value: type,
                child: Text(
                  '$type (${DataCollectionConstants.elementNames[type] ?? ''})',
                  style: const TextStyle(fontSize: 16),
                ),
              )).toList(),
              onChanged: onPersonalityCodeChanged,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStartButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: isLoading ? null : onStartDataCollection,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.purple,
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: isLoading
            ? const SizedBox(
                height: 18,
                width: 18,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : const Text(
                'データ収集開始',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
      ),
    );
  }

  Widget _buildDownloadButton() {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton(
            onPressed: onDownloadCSV,
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
    );
  }
}
