/// A utility class that holds constants for Firebase configuration and keys.
class FirebaseConstants {
  // Private constructor to prevent instantiation.
  FirebaseConstants._();

  // Cloud Functions/Firestore Region
  static const String region = 'asia-northeast1';

  // Cloud Functions Callable Function Names
  static const String generateSignedUrl = 'generate_signed_url';

  // Firestore Collection Names
  static const String jobsCollection = 'jobs';

  // Request/Response Keys
  static const String contentType = 'contentType';
  static const String audioContentType = 'audio/webm';

  // Local constants
  static const String recordFileName = 'voice_record.webm';
}
