import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:firebase_storage/firebase_storage.dart';

class JudgeAndReport {
  final String element;
  final String report;
  final String gemmaJudge;
  final bool gemmaSuccess;
  final String pred_label;

  JudgeAndReport({
    required this.element,
    required this.report,
    required this.gemmaJudge,
    required this.gemmaSuccess,
    required this.pred_label,
  });

  factory JudgeAndReport.fromJson(Map<String, dynamic> json) {
    return JudgeAndReport(
      element: json['element'] ?? 'element enmpty',
      report: json['report'] ?? 'report empty',
      gemmaJudge: json['gemma_judge'] ?? 'gemma-judge enmpty',
      gemmaSuccess: json['gemma_success'] ?? false,
      pred_label: json['pred_label'] ?? '',
    );
  }
}

class ApiService {
  static const String baseUrl =
      kDebugMode ? 'http://localhost:8000/api/v1' : '/api/v1';

    // ここでアップロード機能を追加します
  Future<String?> uploadTextToFirebaseStorage(String text, String fileName) async {
    try {
      final storageRef = FirebaseStorage.instance.ref().child('feedback/$fileName');
      final data = Uint8List.fromList(text.codeUnits);
      final uploadTask = storageRef.putData(data, SettableMetadata(contentType: 'text/plain'));
      final snapshot = await uploadTask.whenComplete(() => null);
      return await snapshot.ref.getDownloadURL();
    } catch (e) {
      print('Upload failed: $e');
      return null;
    }
  }

  Future<String?> _getAuthToken() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      try {
        return await user.getIdToken(true); // Force refresh token
      } catch (e) {
        debugPrint('Failed to get ID token: $e');
        return null;
      }
    }
    return null;
  }

  Future<Map<String, String>> _getHeaders() async {
    final token = await _getAuthToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // 会話を開始
  Future<Map<String, dynamic>> startConversation() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/conversation/start'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to start conversation: ${response.statusCode}');
    }
  }

  // 回答オプションを取得
  Future<Map<String, dynamic>> getOptions() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/conversation/options'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to get options: ${response.statusCode}');
    }
  }

  // 回答を送信
  Future<Map<String, dynamic>> submitAnswer(String answer) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/conversation/answer'),
      headers: headers,
      body: json.encode({'answer': answer}),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to submit answer: ${response.statusCode}');
    }
  }

  // 進捗を取得
  Future<Map<String, dynamic>> getProgress() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/conversation/progress'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to get progress: ${response.statusCode}');
    }
  }

  // 新しい会話を強制的に開始（既存セッションを完了してから新しいセッションを作成）
  Future<Map<String, dynamic>> startNewConversation() async {
    try {
      // 既存のセッションを完了
      await completeAssessment(force: true);
    } catch (e) {
      // 既存セッションがない場合や、完了に失敗した場合は無視して続行
      debugPrint('Failed to complete existing session: $e');
    }

    // 新しい会話を開始
    return await startConversation();
  }

  // 診断を完了
  Future<Map<String, dynamic>> completeAssessment({bool force = false}) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/conversation/complete'),
      headers: headers,
      body: json.encode({'force': force}),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to complete assessment: \\${response.statusCode}');
    }
  }

  // 会話履歴を取得
  Future<Map<String, dynamic>> getConversationHistory() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/conversation/history'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception(
        'Failed to get conversation history: ${response.statusCode}',
      );
    }
  }

  Stream<String> fetchReportStreamFromApi() async* {
    try {
      // サーバーのAPIエンドポイントにリクエストを送信
      final request = http.Request(
        'GET',
        Uri.parse(
          'https://mbti-diagnosis-summary-47665095629.asia-southeast1.run.app/generate-report-stream',
        ),
      );
      final response = await http.Client().send(request);

      String buffer = '';

      // APIからのレスポンスを受け取り、ストリームとして処理
      await for (final chunk in response.stream.transform(utf8.decoder)) {
        buffer += chunk;

        while (buffer.contains('}')) {
          final endOfJson = buffer.indexOf('}') + 1;
          final jsonString = buffer.substring(0, endOfJson);
          buffer = buffer.substring(endOfJson);

          yield jsonString;
        }
      }
    } catch (e) {
      // エラーハンドリング
      print('APIからのデータ取得中にエラーが発生しました: $e');
      yield jsonEncode({"error": "API接続に失敗しました: $e"});
    }
  }
}
