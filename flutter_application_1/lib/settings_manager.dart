import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class AppSettings {
  int stabilityFrames;
  double confidenceThreshold;
  double stabilityThreshold;
  bool allowRepetition;
  bool autoSpeak;
  double speechRate;
  double speechPitch;

  AppSettings({
    this.stabilityFrames = 3,
    this.confidenceThreshold = 0.50,
    this.stabilityThreshold = 0.045,
    this.allowRepetition = false,
    this.autoSpeak = true,
    this.speechRate = 0.5,
    this.speechPitch = 1.0,
  });

  Map<String, dynamic> toJson() => {
        'stabilityFrames': stabilityFrames,
        'confidenceThreshold': confidenceThreshold,
        'stabilityThreshold': stabilityThreshold,
        'allowRepetition': allowRepetition,
        'autoSpeak': autoSpeak,
        'speechRate': speechRate,
        'speechPitch': speechPitch,
      };

  factory AppSettings.fromJson(Map<String, dynamic> json) {
    return AppSettings(
      stabilityFrames: json['stabilityFrames'] ?? 3,
      confidenceThreshold: json['confidenceThreshold'] ?? 0.50,
      stabilityThreshold: json['stabilityThreshold'] ?? 0.045,
      allowRepetition: json['allowRepetition'] ?? false,
      autoSpeak: json['autoSpeak'] ?? true,
      speechRate: json['speechRate'] ?? 0.5,
      speechPitch: json['speechPitch'] ?? 1.0,
    );
  }
}

class SettingsManager {
  static const String _key = 'app_settings';

  static Future<AppSettings> loadSettings() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String? jsonString = prefs.getString(_key);
      
      if (jsonString == null) {
        return AppSettings(); // العودة للإعدادات الافتراضية إذا كان التطبيق يفتح لأول مرة
      }
      
      final Map<String, dynamic> jsonMap = jsonDecode(jsonString);
      return AppSettings.fromJson(jsonMap);
    } catch (e) {
      print("Error loading settings: $e");
      return AppSettings();
    }
  }

  static Future<void> saveSettings(AppSettings settings) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String jsonString = jsonEncode(settings.toJson());
      await prefs.setString(_key, jsonString);
    } catch (e) {
      print("Error saving settings: $e");
    }
  }
}