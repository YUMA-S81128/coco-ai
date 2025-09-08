/// Firebaseの設定とキーの定数を保持するユーティリティクラス
class FirebaseConstants {
  // このクラスはインスタンス化されないように、プライベートコンストラクタを使用
  FirebaseConstants._();

  // Cloud Functions/Firestore のリージョン
  static const String region = 'asia-northeast1';

  // Cloud Functions の呼び出し可能な関数名
  static const String generateSignedUrl = 'generate_signed_url';

  // Firestore のコレクション名
  static const String jobsCollection = 'jobs';

  // リクエスト/レスポンスのキー
  static const String contentType = 'contentType';
  static const String audioContentType = 'audio/webm';

  // ローカル定数
  static const String recordFileName = 'voice_record.webm';
}
