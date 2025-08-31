import 'package:freezed_annotation/freezed_annotation.dart';

part 'app_state.freezed.dart';

/// An enum representing the current status of the application.
enum AppStatus { initial, recording, processing, success, error }

/// A class that holds the entire state of the application.
@freezed
abstract class AppState with _$AppState {
  const factory AppState({
    @Default(AppStatus.initial) AppStatus status,
    String? resultText,
    String? imageUrl,
    String? errorMessage,
  }) = _AppState;
}
