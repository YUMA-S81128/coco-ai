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
        path: 'voice_record.webm',
      );
    } else {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'マイクの使用が許可されていません。',
      );
    }
  }

  /// Stops recording and starts the AI processing.
  Future<void> stopRecordingAndProcess() async {
    // Get the current user ID from the auth service.
    final userId = _ref.read(authServiceProvider).currentUserId;
    if (userId == null) {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: '未ログインの状態では使用できません。',
      );
      return;
    }

    try {
      state = state.copyWith(status: AppStatus.processing);

      final audioPath = await _audioRecorder.stop();
      if (audioPath == null) {
        throw Exception('録音データの保存に失敗しました。');
      }

      // On the web, `stop()` returns a blob URL. We need to fetch its content
      // via an HTTP request to get the audio data as bytes.
      final response = await http.get(Uri.parse(audioPath));
      final audioBytes = response.bodyBytes;

      // 1. Call Cloud Functions to get a signed URL and job ID.
      final functions = _ref.read(_functionsProvider);
      final callable = functions.httpsCallable(
        FirebaseConstants.generateSignedUrl,
      );
      // Pass the 'contentType' argument required by the backend.
      final result = await callable.call<Map<String, dynamic>>({
        FirebaseConstants.contentType: FirebaseConstants.audioContentType,
      });
      // Key for the backend response.
      final uploadUrl = result.data['signedUrl'] as String;
      final jobId = result.data['jobId'] as String;

      final requiredHeaders = Map<String, String>.from(
        result.data['requiredHeaders'] as Map,
      );

      // 2. Upload the audio data to the obtained signed URL.
      await _uploadAudio(uploadUrl, audioBytes, requiredHeaders);

      // 3. Listen for updates on the job document in Firestore.
      _listenToJobUpdates(jobId);
    } on FirebaseFunctionsException catch (e) {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'サーバーとの通信に失敗しました: ${e.message}',
      );
    } catch (e) {
      state = state.copyWith(
        status: AppStatus.error,
        errorMessage: 'エラーが発生しました: ${e.toString()}',
      );
    }
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
        .listen((snapshot) async {
          if (!snapshot.exists) return;

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
            // Do nothing for in-progress statuses.
          }
        });
  }

  @override
  void dispose() {
    _audioRecorder.dispose();
    _jobSubscription?.cancel();
    super.dispose();
  }
}
