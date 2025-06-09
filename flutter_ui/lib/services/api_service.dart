import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api/v1';

  Future<String?> _getAuthToken() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      try {
        return await user.getIdToken(true); // Force refresh token
      } catch (e) {
        print('Failed to get ID token: $e');
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
      await completeAssessment();
    } catch (e) {
      // 既存セッションがない場合や、完了に失敗した場合は無視して続行
      debugPrint('Failed to complete existing session: $e');
    }

    // 新しい会話を開始
    return await startConversation();
  }

  // 診断を完了
  Future<Map<String, dynamic>> completeAssessment() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('$baseUrl/conversation/complete'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to complete assessment: ${response.statusCode}');
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
      throw Exception('Failed to get conversation history: ${response.statusCode}');
    }
  }
}
