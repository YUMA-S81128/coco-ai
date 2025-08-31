import 'dart:developer';

import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// A provider for the [StorageService].
final storageServiceProvider = Provider((ref) => StorageService());

/// A service class for interacting with Firebase Cloud Storage.
class StorageService {
  final _storage = FirebaseStorage.instance;

  /// Retrieves a downloadable HTTPS URL from a GCS URI (gs://...).
  ///
  /// Returns an empty string if the URL cannot be retrieved, and logs the error.
  Future<String> getDownloadUrlFromGsPath(String gsPath) async {
    if (gsPath.isEmpty) {
      return '';
    }
    try {
      final ref = _storage.refFromURL(gsPath);
      return await ref.getDownloadURL();
    } catch (e, s) {
      log(
        'Failed to get download URL from GCS path.',
        error: e,
        stackTrace: s,
        name: 'StorageService',
      );
      return '';
    }
  }
}
