// Data collection parameters
class DataCollectionConstants {
  static const int questionsPerElement = 10; // 10 questions per MBTI element
  static const int totalElements = 4;         // 4 MBTI elements (Energy, Mind, Nature, Tactics)
  static const int cyclesPerCollection = 1;
  static const int totalPhases = totalElements * cyclesPerCollection; // 4 phases total

  // List of 16 MBTI personality codes
  static const List<String> personalityTypes = [
    'ISTJ','ISFJ','INFJ','INTJ',
    'ISTP','ISFP','INFP','INTP',
    'ESTP','ESFP','ENFP','ENTP',
    'ESTJ','ESFJ','ENFJ','ENTJ'
  ];

  static const Map<String, String> elementNames = {
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

  static const List<String> elementTypes = [
    'エネルギー (I/E)',
    '情報収集 (N/S)',
    '意思決定 (T/F)',
    '外界への態度 (J/P)'
  ];
}
