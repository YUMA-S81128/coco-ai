import 'package:app/constants/firebase_constants.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:cloud_functions/cloud_functions.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart' show kIsWeb, kDebugMode, debugPrint;

/// FirebaseFirestore のインスタンスを提供するプロバイダー
final firestoreProvider = Provider((ref) {
  final firestore = FirebaseFirestore.instance;
  // デバッグモードの場合、ローカルのFirestoreエミュレータに接続
  if (kDebugMode) {
    try {
      firestore.useFirestoreEmulator('localhost', 8080);
    } catch (e) {
      // ホットリスタートなどで既に設定済みの場合に発生するエラーを無視
      debugPrint('Firestoreエミュレータの再設定をスキップしました: $e');
    }
  }
  return firestore;
});

/// FirebaseStorage のインスタンスを提供するプロバイダー
final firebaseStorageProvider = Provider((ref) {
  final storage = FirebaseStorage.instance;
  // デバッグモードの場合、ローカルのStorageエミュレータに接続
  if (kDebugMode) {
    try {
      storage.useStorageEmulator('localhost', 9199);
    } catch (e) {
      debugPrint('Storageエミュレータの再設定をスキップしました: $e');
    }
  }
  return storage;
});

/// FirebaseFunctions のインスタンスを提供するプロバイダー
final functionsProvider = Provider((ref) {
  // --- 開発モード（エミュレータ） ---
  // プラットフォームに関わらず、デバッグモードの場合はローカルエミュレータに接続
  if (kDebugMode) {
    final functions = FirebaseFunctions.instanceFor(
      region: FirebaseConstants.region,
    );
    functions.useFunctionsEmulator('localhost', 5001);
    return functions;
  }

  // --- 本番モード ---
  // Webの本番環境では、Hostingのrewritesを経由させるため、
  // region引数にHostingのURLを渡す
  if (kIsWeb) {
    return FirebaseFunctions.instanceFor(
      region: 'https://${FirebaseConstants.functionsOriginHost}',
    );
  }

  // モバイルアプリなど、Web以外の本番環境では通常のリージョンを指定
  return FirebaseFunctions.instanceFor(region: FirebaseConstants.region);
});
