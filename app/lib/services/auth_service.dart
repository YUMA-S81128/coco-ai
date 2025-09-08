import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// [AuthService] を提供するプロバイダー
final authServiceProvider = Provider(
  (ref) => AuthService(FirebaseAuth.instance),
);

/// 認証を処理するためのサービスクラス
class AuthService {
  final FirebaseAuth _auth;

  AuthService(this._auth);

  /// 現在のユーザーのIDを返す
  /// サインインしていない場合はnullを返す
  String? get currentUserId => _auth.currentUser?.uid;
}
