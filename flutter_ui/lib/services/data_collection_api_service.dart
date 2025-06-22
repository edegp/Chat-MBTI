import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

class DataCollectionApiService {
  static const String baseUrl = kDebugMode
      ? 'http://localhost:8000/api/v1'
      : '/api/v1';

  // Create a mock token for data collection
  static const String mockToken = 'data_collection_user';

  Future<Map<String, String>> _getHeaders() async {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $mockToken',
    };
  }

  // 会話を開始 (element_id指定対応)
  Future<Map<String, dynamic>> startConversation({int? elementId}) async {
    final headers = await _getHeaders();
    final uri = elementId != null
      ? Uri.parse('$baseUrl/data-collection/conversation/start?element_id=$elementId')
      : Uri.parse('$baseUrl/data-collection/conversation/start');
    final response = await http.get(uri, headers: headers);
    if (response.statusCode == 200) return json.decode(response.body);
    throw Exception('Failed to start conversation: ${response.statusCode}');
  }

  // 回答オプションを取得
  Future<Map<String, dynamic>> getOptions() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/data-collection/conversation/options'),
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
      Uri.parse('$baseUrl/data-collection/conversation/answer'),
      headers: headers,
      body: json.encode({'answer': answer}),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to submit answer: ${response.statusCode}');
    }
  }

  // 新しい会話を強制的に開始（element_id指定対応）
  Future<Map<String, dynamic>> startNewConversation({int? elementId}) async {
    try {
      // 既存のセッションを完了
      await completeAssessment();
    } catch (e) {
      // 既存セッションがない場合や、完了に失敗した場合は無視して続行
      debugPrint('Failed to complete existing session: $e');
    }

    // 新しい会話を開始
    return await startConversation(elementId: elementId);
  }

  // 診断を完了
  Future<Map<String, dynamic>> completeAssessment() async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/data-collection/conversation/complete'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to complete assessment: ${response.statusCode}');
    }
  }

  // CSVデータをGCSにアップロード
  Future<bool> uploadCsvToGcs({
    required String participantName,
    required String personalityCode,
    required String csvContent,
    int? elementId,
    int? cycleNumber,
  }) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/data-collection/upload'),
      headers: headers,
      body: json.encode({
        'participant_name': participantName,
        'personality_code': personalityCode,
        'csv_content': csvContent,
        // optional parameters
        'element_id': elementId,
        'cycle_number': cycleNumber,
      }),
    );

    if (response.statusCode == 200) {
      return true;
    } else {
      debugPrint('Failed to upload CSV: ${response.body}');
      return false;
    }
  }

  // 最後の回答を取り消す（サーバー状態を巻き戻す）
  Future<Map<String, dynamic>> undoLastAnswer() async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('$baseUrl/data-collection/conversation/undo'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to undo last answer: ${response.statusCode}');
    }
  }
}
