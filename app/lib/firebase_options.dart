import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart' show kDebugMode;

/// Firebaseプロジェクトの設定を環境変数から読み込み、
/// FirebaseOptionsオブジェクトを生成するためのクラス。
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    // --dart-define-from-fileで渡された環境変数を取得
    const apiKey = String.fromEnvironment('FIREBASE_API_KEY');
    assert(apiKey.isNotEmpty, 'FIREBASE_API_KEY must be provided.');
    const appId = String.fromEnvironment('FIREBASE_APP_ID');
    assert(appId.isNotEmpty, 'FIREBASE_APP_ID must be provided.');
    const messagingSenderId = String.fromEnvironment(
      'FIREBASE_MESSAGING_SENDER_ID',
    );
    assert(
      messagingSenderId.isNotEmpty,
      'FIREBASE_MESSAGING_SENDER_ID must be provided.',
    );
    const projectId = String.fromEnvironment('FIREBASE_PROJECT_ID');
    assert(projectId.isNotEmpty, 'FIREBASE_PROJECT_ID must be provided.');
    const storageBucket = String.fromEnvironment('FIREBASE_STORAGE_BUCKET');
    assert(
      storageBucket.isNotEmpty,
      'FIREBASE_STORAGE_BUCKET must be provided.',
    );
    const authDomain = String.fromEnvironment('FIREBASE_AUTH_DOMAIN');
    assert(authDomain.isNotEmpty, 'FIREBASE_AUTH_DOMAIN must be provided.');

    // Web以外のプラットフォーム用の設定もここに追加可能
    // if (kIsWeb) { ... } else if (defaultTargetPlatform == TargetPlatform.iOS) { ... }

    return const FirebaseOptions(
      apiKey: apiKey,
      appId: appId,
      messagingSenderId: messagingSenderId,
      projectId: projectId,
      storageBucket: storageBucket,
      authDomain: authDomain,
    );
  }
}
