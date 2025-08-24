import 'package:flutter/foundation.dart';

/// アプリケーションの現在の状態を示すenum
enum AppStatus {
  initial, // 初期状態
  recording, // 録音中
  processing, // AIが処理中
  success, // 成功（結果表示）
  error, // エラー発生
}

/// アプリケーション全体の状態を保持するクラス
@immutable
class AppState {
  const AppState({
    this.status = AppStatus.initial,
    this.resultText,
    this.imageUrl,
    this.errorMessage,
  });

  final AppStatus status;
  final String? resultText;
  final String? imageUrl;
  final String? errorMessage;

  AppState copyWith({
    AppStatus? status,
    String? resultText,
    String? imageUrl,
    String? errorMessage,
  }) {
    return AppState(
      status: status ?? this.status,
      resultText: resultText ?? this.resultText,
      imageUrl: imageUrl ?? this.imageUrl,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

