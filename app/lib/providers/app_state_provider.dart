import 'dart:async';
import 'dart:typed_data';

import 'package:app/providers/firebase_providers.dart';
import 'package:app/constants/firebase_constants.dart';
import 'package:app/services/auth_service.dart';
import 'package:app/models/signed_url_response.dart';
import 'package:app/models/app_state.dart';
import 'package:app/models/job.dart';
import 'package:app/services/storage_service.dart';
import 'package:cloud_functions/cloud_functions.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:record/record.dart';

/// アプリケーションの状態（AppState）を管理するStateNotifierProvider
final appStateProvider = StateNotifierProvider<AppStateNotifier, AppState>((
  ref,
) {
  return AppStateNotifier(ref);
});

/// アプリケーションのビジネスロジックと状態管理を担当するクラス
class AppStateNotifier extends StateNotifier<AppState> {
  final _audioRecorder = AudioRecorder();
  StreamSubscription? _jobSubscription;
  final Ref _ref;

  AppStateNotifier(this._ref) : super(const AppState());

  /// 音声録音を開始
  Future<void> startRecording() async {
    // 録音を開始する前に、利用可能な入力デバイス（マイク）が存在するかを確認する
    // これにより、物理的にマイクがない場合に即座にエラーを返すことができる
    final devices = await _audioRecorder.listInputDevices();
    if (devices.isEmpty) {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'マイクが見つかりませんでした。PCにマイクが接続されているか、OSのプライバシー設定を確認してください。',
      );
      return;
    }

    try {
      // 録音を開始する。Webでは、このメソッドがマイクの使用許可を求めるプロンプトをトリガーする
      await _audioRecorder.start(
        const RecordConfig(encoder: AudioEncoder.opus, sampleRate: 48000),
        path: FirebaseConstants.recordFileName,
      );

      // 録音が正常に開始されたことを確認し、UIの状態を更新
      if (await _audioRecorder.isRecording()) {
        state = state.copyWith(status: AppStatus.recording);
      } else {
        // start()が成功しても録音状態にならなかった場合のフォールバック
        throw Exception('レコーダーが録音状態への移行に失敗しました。');
      }
    } catch (e) {
      final errorString = e.toString().toLowerCase();
      String errorMessage;

      // ユーザーがマイクの使用を拒否した場合
      if (errorString.contains('notallowederror') ||
          errorString.contains('permission denied')) {
        errorMessage = 'マイクの使用が許可されませんでした。ブラウザのアドレスバーのアイコンからサイトの設定を確認してください。';
      } else {
        // その他の予期しないエラー
        errorMessage = '録音の開始に失敗しました。ページを再読み込みしてお試しください。';
      }
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: errorMessage,
      );
    }
  }

  /// 録音を停止し、AI処理を開始する
  /// このメソッドはプロセス全体を統括する:
  /// 1. 録音を停止し、音声データを取得
  /// 2. バックエンドから安全なアップロードURLとジョブIDを取得
  /// 3. 音声ファイルを直接Cloud Storageにアップロード
  /// 4. Firestoreからリアルタイムでジョブステータスの更新リッスンを開始する
  Future<void> stopRecordingAndProcess() async {
    // 処理を開始する前に、レコーダーが実際に録音中かを確認する
    if (state.status != AppStatus.recording) {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: '録音されていませんでした。もう一度お試しください。',
      );
      // エラーメッセージ表示後、UIを初期状態に戻す
      state = state.copyWith(status: AppStatus.initial);
      return;
    }
    // AuthServiceから現在のユーザーIDを取得
    final userId = _ref.read(authServiceProvider).currentUserId;
    if (userId == null) {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'ログインが必要です。',
      );
      return;
    }

    state = state.copyWith(status: AppStatus.processing);

    try {
      // 1. 録音を停止し、音声データをバイト配列として取得
      final audioBytes = await _stopAndGetAudioBytes();

      // 2. Cloud Functionsを呼び出して、署名付きURLとジョブIDを取得
      final uploadInfo = await _getSignedUrlAndJobId();
      final uploadUrl = uploadInfo['uploadUrl'] as String;
      final jobId = uploadInfo['jobId'] as String;
      final requiredHeaders =
          uploadInfo['requiredHeaders'] as Map<String, String>;

      // 3. 取得した署名付きURLに音声データをアップロード
      await _uploadAudio(uploadUrl, audioBytes, requiredHeaders);

      // 4. Firestoreのジョブドキュメントの更新をリッスンする
      _listenToJobUpdates(jobId);
    } on FirebaseFunctionsException catch (e) {
      _handleFirebaseFunctionsError(e);
    } catch (e) {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'エラーが発生しました: ${e.toString()}',
      );
    }
  }

  /// 音声レコーダーを停止し、録音された音声データをバイト配列として返す
  Future<Uint8List> _stopAndGetAudioBytes() async {
    final audioPath = await _audioRecorder.stop();
    if (audioPath == null) {
      throw Exception('録音データがありません。録音が正常に開始されなかった可能性があります。');
    }

    // Webでは、`stop()`はblob URLを返します。HTTPリクエストでその内容を取得し、
    // 音声データをバイト配列として得る必要がある
    try {
      final response = await http.get(Uri.parse(audioPath));
      if (response.statusCode == 200) {
        return response.bodyBytes;
      } else {
        throw Exception('録音データの取得に失敗しました (HTTP ${response.statusCode})');
      }
    } catch (e) {
      throw Exception('録音データの読み込み中にエラーが発生しました: $e');
    }
  }

  /// 署名付きURLとジョブ詳細を取得するためにCloud Functionを呼び出す
  Future<Map<String, dynamic>> _getSignedUrlAndJobId() async {
    final functions = _ref.read(functionsProvider);
    final callable = functions.httpsCallable(
      FirebaseConstants.generateSignedUrl,
    );

    final result = await callable.call<Map<String, dynamic>>({
      FirebaseConstants.contentType: FirebaseConstants.audioContentType,
    });

    try {
      final response = SignedUrlResponse.fromJson(result.data);
      return {
        'uploadUrl': response.signedUrl,
        'jobId': response.jobId,
        'requiredHeaders': response.requiredHeaders,
      };
    } catch (e) {
      // JSONのパースやモデルの検証に失敗した場合
      throw Exception('サーバーからのレスポンス形式が正しくありません: $e');
    }
  }

  /// Firebase Functionsからの特定のエラーを処理し、ユーザーフレンドリーな
  /// メッセージで状態を更新する
  void _handleFirebaseFunctionsError(FirebaseFunctionsException e) {
    String message;
    switch (e.code) {
      case 'unauthenticated':
        message = '認証が必要です。再度ログインしてください。';
        break;
      case 'invalid-argument':
        message = 'リクエスト内容が正しくありません。';
        break;
      case 'internal':
        message = 'サーバーで問題が発生しました。しばらくしてからもう一度お試しください。';
        break;
      default:
        message = 'サーバーとの通信に失敗しました: ${e.message ?? '不明なエラー'}';
    }
    state = state.copyWith(status: AppStatus.error, errorMessage: message);
  }

  /// 署名付きURLを使用してCloud Storageにファイルをアップロードする
  Future<void> _uploadAudio(
    String url,
    Uint8List data,
    Map<String, String> headers,
  ) async {
    final response = await http.put(
      Uri.parse(url),
      headers: headers,
      body: data,
    );
    if (response.statusCode != 200) {
      throw Exception('ファイルのアップロードに失敗しました: ${response.body}');
    }
  }

  /// Firestoreのジョブの更新をリッスンする
  void _listenToJobUpdates(String jobId) {
    _jobSubscription?.cancel();
    _jobSubscription = _ref
        .read(firestoreProvider)
        .collection(FirebaseConstants.jobsCollection)
        .doc(jobId)
        .snapshots()
        .listen(
          (snapshot) async {
            if (!snapshot.exists) return;

            try {
              // 安全なJobモデルに変換する
              final job = Job.fromFirestore(snapshot);

              switch (job.status) {
                case JobStatus.completed:
                  // GCSパスからダウンロードURLを取得する
                  final imageUrl = job.imageGcsPath != null
                      ? await _ref
                            .read(storageServiceProvider)
                            .getDownloadUrlFromGsPath(job.imageGcsPath!)
                      : null;

                  state = state.copyWith(
                    status: AppStatus.success,
                    resultText: job.childExplanation,
                    imageUrl: imageUrl,
                  );
                  _jobSubscription?.cancel();
                  break;
                case JobStatus.error:
                  state = state.copyWith(
                    status: AppStatus.error,
                    errorMessage: job.errorMessage ?? '不明なエラーが発生しました。',
                  );
                  _jobSubscription?.cancel();
                  break;
                default:
                // 'processing'、'illustrating'などの進行中のステータスでは何もしない
              }
            } catch (e) {
              // データ解析またはURL取得中の潜在的なエラーを処理する
              state = state.copyWith(
                status: AppStatus.error,
                errorMessage: '結果の処理中にエラーが発生しました: $e',
              );
              _jobSubscription?.cancel();
            }
          },
          onError: (error) {
            state = state.copyWith(
              status: AppStatus.error,
              errorMessage: 'データの同期に失敗しました: $error',
            );
            _jobSubscription?.cancel();
          },
        );
  }

  @override
  void dispose() {
    _audioRecorder.dispose();
    _jobSubscription?.cancel();
    super.dispose();
  }
}
