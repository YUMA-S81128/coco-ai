import 'dart:developer';

import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// [StorageService] を提供するプロバイダー
final storageServiceProvider = Provider((ref) => StorageService());

/// Firebase Cloud Storageとやり取りするためのサービスクラス
class StorageService {
  final _storage = FirebaseStorage.instance;

  /// GCS URI (gs://...) からダウンロード可能なHTTPS URLを取得
  ///
  /// URLが取得できない場合は空文字列を返し、エラーをログに記録
  Future<String> getDownloadUrlFromGsPath(String gsPath) async {
    if (gsPath.isEmpty) {
      return '';
    }
    try {
      final ref = _storage.refFromURL(gsPath);
      return await ref.getDownloadURL();
    } catch (e, s) {
      log(
        'GCSパスからのダウンロードURLの取得に失敗しました。',
        error: e,
        stackTrace: s,
        name: 'StorageService',
      );
      return '';
    }
  }
}
