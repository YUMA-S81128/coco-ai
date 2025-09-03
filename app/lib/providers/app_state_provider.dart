import 'dart:async';
import 'dart:typed_data';

import 'package:app/constants/firebase_constants.dart';
import 'package:app/services/auth_service.dart';
import 'package:app/models/app_state.dart';
import 'package:app/models/job.dart';
import 'package:app/services/storage_service.dart';
import 'package:cloud_functions/cloud_functions.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:record/record.dart';

/// A provider for the Firebase Functions instance.
final _functionsProvider = Provider(
  (ref) => FirebaseFunctions.instanceFor(region: FirebaseConstants.region),
);

/// A provider for the Firestore instance.
final _firestoreProvider = Provider((ref) => FirebaseFirestore.instance);

/// A StateNotifierProvider that manages the application's state.
final appStateProvider = StateNotifierProvider<AppStateNotifier, AppState>((
  ref,
) {
  return AppStateNotifier(ref);
});

class AppStateNotifier extends StateNotifier<AppState> {
  final _audioRecorder = AudioRecorder();
  StreamSubscription? _jobSubscription;
  final Ref _ref;

  AppStateNotifier(this._ref) : super(const AppState());

  /// Starts the audio recording.
  Future<void> startRecording() async {
    if (await _audioRecorder.hasPermission()) {
      state = state.copyWith(status: AppStatus.recording);
      await _audioRecorder.start(
        const RecordConfig(
          // Specify the Opus codec used in the WebM container.
          encoder: AudioEncoder.opus,
          // Match the sample rate with the backend's Speech-to-Text configuration.
          sampleRate: 48000,
        ),
        // A path is required but not used on the web. The recording is stored in memory.
        path: FirebaseConstants.recordFileName,
      );
    } else {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'マイクの使用が許可されていません。',
      );
    }
  }

  /// Stops recording and starts the AI processing.
  /// This method orchestrates the entire process:
  /// 1. Stops the recording and retrieves the audio data.
  /// 2. Obtains a secure upload URL and a job ID from the backend.
  /// 3. Uploads the audio file directly to Cloud Storage.
  /// 4. Begins listening for real-time job status updates from Firestore.
  Future<void> stopRecordingAndProcess() async {
    // Get the current user ID from the auth service.
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
      // 1. Stop recording and get the audio data as bytes.
      final audioBytes = await _stopAndGetAudioBytes();

      // 2. Call Cloud Functions to get a signed URL and job ID.
      final uploadInfo = await _getSignedUrlAndJobId();
      final uploadUrl = uploadInfo['uploadUrl'] as String;
      final jobId = uploadInfo['jobId'] as String;
      final requiredHeaders =
          uploadInfo['requiredHeaders'] as Map<String, String>;

      // 3. Upload the audio data to the obtained signed URL.
      await _uploadAudio(uploadUrl, audioBytes, requiredHeaders);

      // 4. Listen for updates on the job document in Firestore.
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

  /// Stops the audio recorder and returns the recorded audio data as bytes.
  Future<Uint8List> _stopAndGetAudioBytes() async {
    final audioPath = await _audioRecorder.stop();
    if (audioPath == null) {
      throw Exception('録音データの保存に失敗しました。');
    }

    // On the web, `stop()` returns a blob URL. We need to fetch its content
    // via an HTTP request to get the audio data as bytes.
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

  /// Calls the Cloud Function to get a signed URL and job details.
  Future<Map<String, dynamic>> _getSignedUrlAndJobId() async {
    final functions = _ref.read(_functionsProvider);
    final callable = functions.httpsCallable(
      FirebaseConstants.generateSignedUrl,
    );

    final result = await callable.call<Map<String, dynamic>>({
      FirebaseConstants.contentType: FirebaseConstants.audioContentType,
    });

    final data = result.data;
    final uploadUrl = data['signedUrl'] as String?;
    final jobId = data['jobId'] as String?;
    final requiredHeaders = data['requiredHeaders'] as Map?;

    if (uploadUrl == null || jobId == null || requiredHeaders == null) {
      throw Exception('サーバーからのレスポンス形式が正しくありません。');
    }

    return {
      'uploadUrl': uploadUrl,
      'jobId': jobId,
      'requiredHeaders': Map<String, String>.from(requiredHeaders),
    };
  }

  /// Handles specific errors from Firebase Functions and updates the state
  /// with user-friendly messages.
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

  /// Uploads a file to Cloud Storage using a signed URL.
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

  /// Listens for updates on a job in Firestore.
  void _listenToJobUpdates(String jobId) {
    _jobSubscription?.cancel();
    _jobSubscription = _ref
        .read(_firestoreProvider)
        .collection(FirebaseConstants.jobsCollection)
        .doc(jobId)
        .snapshots()
        .listen(
          (snapshot) async {
            if (!snapshot.exists) return;

            try {
              // Convert to a safe Job model.
              final job = Job.fromFirestore(snapshot);

              switch (job.status) {
                case JobStatus.completed:
                  // Get the download URL from the GCS path.
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
                // Do nothing for in-progress statuses like 'processing', 'illustrating', etc.
              }
            } catch (e) {
              // Handle potential errors during data parsing or URL fetching.
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
