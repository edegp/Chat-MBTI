import 'dart:convert';
import 'package:csv/csv.dart';
import 'package:universal_html/html.dart' as html;
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/data_collection_api_service.dart';
import '../constants/data_collection_constants.dart';

class DataCollectionController {
  final DataCollectionApiService _apiService = DataCollectionApiService();

  // Helper methods
  int getCurrentElementId(int currentPhase) {
    return ((currentPhase - 1) % DataCollectionConstants.totalElements) + 1;
  }

  String getCurrentElementType(int currentPhase) {
    final elementIndex = ((currentPhase - 1) % DataCollectionConstants.totalElements);
    return DataCollectionConstants.elementTypes[elementIndex];
  }

  int getCurrentCycle(int currentPhase) {
    return ((currentPhase - 1) ~/ DataCollectionConstants.totalElements) + 1;
  }

  // API calls
  Future<Map<String, dynamic>> startNewConversation({int? elementId}) async {
    return await _apiService.startNewConversation(elementId: elementId);
  }

  Future<Map<String, dynamic>> getOptions() async {
    return await _apiService.getOptions();
  }

  Future<Map<String, dynamic>> submitAnswer(String answer) async {
    return await _apiService.submitAnswer(answer);
  }

  Future<Map<String, dynamic>> undoLastAnswer({int steps = 1}) async {
    return await _apiService.undoLastAnswer(steps: steps);
  }

  // CSV operations
  void downloadCSV({
    required List<Map<String, dynamic>> collectedData,
    required String? participantName,
    required String? personalityCode,
  }) {
    if (collectedData.isEmpty) return;
    if (!kIsWeb) return;

    // Prepare CSV data
    List<List<dynamic>> csvData = [
      // Header including personality code
      ['Participant Name', 'Personality Code', 'Phase', 'Element Type', 'Cycle Number', 'Question Number', 'Question', 'Answer', 'Timestamp', 'Session ID']
    ];

    // Add data rows
    for (var item in collectedData) {
      final phase = item['phase'] as int;
      final idx = (phase - 1) % DataCollectionConstants.totalElements;
      final codeLetter = (personalityCode != null && personalityCode.length > idx)
          ? personalityCode[idx]
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
      ..download = 'mbti_data_collection_${participantName ?? 'anonymous'}_all_${DateTime.now().toIso8601String().replaceAll(RegExp(r'[:\-T\.]'), '').substring(0, 15)}.csv';
    html.document.body?.children.add(anchor);
    anchor.click();
    html.document.body?.children.remove(anchor);
    html.Url.revokeObjectUrl(url);
  }

  Future<bool> uploadCsvToGcs({
    required List<Map<String, dynamic>> collectedData,
    required String? participantName,
    required String? personalityCode,
  }) async {
    if (collectedData.isEmpty) return false;

    try {
      // Prepare CSV data
      List<List<dynamic>> csvData = [
        ['Participant Name', 'Phase', 'Element Type', 'Cycle Number', 'Question Number', 'Question', 'Answer', 'Timestamp', 'Session ID']
      ];
      for (var item in collectedData) {
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

      return await _apiService.uploadCsvToGcs(
        participantName: participantName ?? 'anonymous',
        personalityCode: personalityCode ?? '',
        csvContent: csvString,
      );
    } catch (e) {
      return false;
    }
  }

  Future<void> uploadPhaseCsvToGcs({
    required int phaseNumber,
    required List<Map<String, dynamic>> currentSessionData,
    required String? participantName,
    required String? personalityCode,
  }) async {
    final phaseData = List<Map<String, dynamic>>.from(currentSessionData);
    if (phaseData.isEmpty) return;

    List<List<dynamic>> csvData = [
      ['Participant Name', 'Phase', 'Element Type', 'Cycle Number', 'Question Number', 'Question', 'Answer', 'Timestamp', 'Session ID']
    ];

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
      participantName: participantName ?? 'anonymous',
      personalityCode: personalityCode ?? '',
      csvContent: csvString,
      elementId: ((phaseNumber - 1) % DataCollectionConstants.totalElements) + 1,
      cycleNumber: getCurrentCycle(phaseNumber),
    );
  }

  // SharedPreferences operations
  Future<void> saveProgressToPrefs({
    required String? participantName,
    required String? personalityCode,
    required int currentPhase,
    required List<Map<String, dynamic>> collectedData,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final saveData = jsonEncode({
      'participantName': participantName,
      'personalityCode': personalityCode,
      'currentPhase': currentPhase,
      'collectedData': collectedData,
    });
    await prefs.setString('mbti_data_collection_progress', saveData);
  }

  Future<Map<String, dynamic>?> restoreProgressFromPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final saveData = prefs.getString('mbti_data_collection_progress');
    if (saveData != null) {
      try {
        return jsonDecode(saveData);
      } catch (e) {
        return null;
      }
    }
    return null;
  }

  Future<void> clearProgressPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('mbti_data_collection_progress');
  }

  // Add alias for clearPrefs to match usage
  Future<void> clearPrefs() async {
    await clearProgressPrefs();
  }

  // Add signOut method for consistency
  Future<void> signOut() async {
    // Clear any stored preferences
    await clearProgressPrefs();
    // Additional sign out logic can be added here if needed
  }
}
