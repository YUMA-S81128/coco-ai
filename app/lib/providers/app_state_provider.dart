import 'dart:async';
import 'dart:typed_data';

import 'package:app/models/app_state.dart';
import 'package:cloud_functions/cloud_functions.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:record/record.dart';

/// アプリケーションの状態を管理するStateNotifierProvider
final appStateProvider = StateNotifierProvider<AppStateNotifier, AppState>((ref) {
  return AppStateNotifier();
});

class AppStateNotifier extends StateNotifier<AppState> {
  AppStateNotifier() : super(const AppState());

  final _audioRecorder = AudioRecorder();
  StreamSubscription? _jobSubscription;

  /// 録音を開始する
  Future<void> startRecording() async {
    // マイクのパーミッションを確認
    if (await _audioRecorder.hasPermission()) {
      state = state.copyWith(status: AppStatus.recording);
      // TODO: Webでの録音形式を適切なもの（例: webm）に設定する必要がある
      await _audioRecorder.start(const RecordConfig(), path: 'voice_record');
    } else {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'マイクの使用が許可されていません。',
      );
    }
  }

  /// 録音を停止し、AI処理を開始する
  Future<void> stopRecordingAndProcess() async {
    try {
      state = state.copyWith(status: AppStatus.processing);

      final audioPath = await _audioRecorder.stop();
      if (audioPath == null) {
        throw Exception('録音データの保存に失敗しました。');
      }

      // Webではファイルパスではなくメモリ上のデータとして扱う
      // recordパッケージのWeb実装に依存
      final response = await http.get(Uri.parse(audioPath));
      final audioBytes = response.bodyBytes;

      // 1. Cloud Functionsを呼び出して、署名付きURLとジョブIDを取得
      final functions = FirebaseFunctions.instanceFor(region: 'asia-northeast1');
      final callable = functions.httpsCallable('generate_signed_url');
      // バックエンドが要求する 'contentType' を引数で渡す
      final result = await callable.call<Map<String, dynamic>>({
        'contentType': 'audio/webm', // Webでの録音形式
      });
      final uploadUrl = result.data['uploadUrl'] as String;
      final jobId = result.data['jobId'] as String;

      // 2. 取得した署名付きURLに音声データをアップロード
      await _uploadAudio(uploadUrl, audioBytes);

      // 3. Firestoreのジョブドキュメントを監視
      _listenToJobUpdates(jobId);
    } catch (e) {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'エラーが発生しました: ${e.toString()}',
      );
    }
  }

  /// 署名付きURLを使用してCloud Storageにファイルをアップロードする
  Future<void> _uploadAudio(String url, Uint8List data) async {
    final response = await http.put(
      Uri.parse(url),
      headers: {'Content-Type': 'audio/webm'}, // callableに渡したcontentTypeと合わせる
      body: data,
    );
    if (response.statusCode != 200) {
      throw Exception('ファイルのアップロードに失敗しました: ${response.body}');
    }
  }

  /// Firestoreのジョブの更新を監視する
  void _listenToJobUpdates(String jobId) {
    _jobSubscription?.cancel();
    // TODO: Firestoreのコレクション名とフィールド名を実際のものに合わせる
    _jobSubscription = FirebaseFirestore.instance
        .collection('jobs')
        .doc(jobId)
        .snapshots()
        .listen((snapshot) {
      if (!snapshot.exists) return;

      final data = snapshot.data()!;
      final jobStatus = data['status'] as String;

      // バックエンドの実装に合わせてステータス名を修正する (例: 'success')
      if (jobStatus == 'success') {
        state = state.copyWith(
          status: AppStatus.success,
          resultText: data['resultText'] as String?,
          imageUrl: data['imageUrl'] as String?,
        );
        _jobSubscription?.cancel();
      } else if (jobStatus == 'error') {
        state = state.copyWith(
          status: AppStatus.error,
          errorMessage: data['errorMessage'] as String?,
        );
        _jobSubscription?.cancel();
      }
      // 'processing'などの途中経過ステータスもここでハンドリング可能
    });
  }

  @override
  void dispose() {
    _audioRecorder.dispose();
    _jobSubscription?.cancel();
    super.dispose();
  }
}
