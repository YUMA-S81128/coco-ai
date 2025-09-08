import 'package:freezed_annotation/freezed_annotation.dart';

part 'app_state.freezed.dart';

/// アプリケーションの現在の状態を表すenum
///
/// - [initial]: 初期状態
/// - [recording]: 録音中
/// - [processing]: AI処理中
/// - [success]: 処理成功
/// - [error]: エラー発生
enum AppStatus { initial, recording, processing, success, error }

/// アプリケーション全体のUI状態を保持するクラス
@freezed
abstract class AppState with _$AppState {
  const factory AppState({
    /// 現在のアプリの状態
    @Default(AppStatus.initial) AppStatus status,

    /// AIによって生成された解説文
    String? resultText,

    /// AIによって生成されたイラストのURL
    String? imageUrl,

    /// エラーが発生した場合のメッセージ
    String? errorMessage,
  }) = _AppState;
}
